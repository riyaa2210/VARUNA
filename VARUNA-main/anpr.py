# ===================================================================================
# anpr.py — Feature 2: Automatic Number Plate Recognition + SQLite Logging
#
# Pipeline:
#   1. Receive a vehicle bounding-box crop from main.py
#   2. Pre-process crop for better OCR (grayscale, CLAHE, threshold)
#   3. Run EasyOCR to extract text
#   4. Filter result with regex for Indian plate format (e.g. MH12AB1234)
#   5. Write confirmed plate reads to SQLite: varuna_logs.db
#
# SQLite schema (vehicles table):
#   id, timestamp, plate_text, confidence, incident_type, image_path
#
# Graceful fallback: if easyocr is not installed, ANPR is silently disabled.
# ===================================================================================

import cv2
import re
import sqlite3
import os
import time
import logging
from datetime import datetime

# --- Try importing EasyOCR (optional dependency) ---
try:
    import easyocr
    _READER = None  # Lazy-loaded on first use to avoid blocking startup
    ANPR_AVAILABLE = True
    print("[ANPR] EasyOCR available — ANPR enabled.")
except ImportError:
    ANPR_AVAILABLE = False
    _READER = None
    print("[ANPR] EasyOCR not installed — ANPR disabled. Run: pip install easyocr")

# --- Config ---
DB_PATH = os.path.join(os.path.dirname(__file__), "varuna_logs.db")

# Indian plate regex patterns
# Standard: MH12AB1234, KA05MX9988, DL3CAF9012
# BH series: 22BH1234AA
PLATE_PATTERNS = [
    re.compile(r'\b[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{4}\b'),   # Standard state plates
    re.compile(r'\b\d{2}BH\d{4}[A-Z]{1,2}\b'),             # BH-series
    re.compile(r'\b[A-Z]{2}\d{2}[A-Z]{2}\d{4}\b'),          # Alternate format
]


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def _get_connection() -> sqlite3.Connection:
    """Open (or reuse) the SQLite database and ensure schema exists."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp     TEXT    NOT NULL,
            plate_text    TEXT    NOT NULL,
            confidence    REAL    DEFAULT 0,
            incident_type TEXT    DEFAULT 'None',
            image_path    TEXT    DEFAULT '',
            lat           REAL    DEFAULT 0,
            lon           REAL    DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp     TEXT    NOT NULL,
            incident_type TEXT    NOT NULL,
            severity      TEXT    DEFAULT 'Unknown',
            lat           REAL    DEFAULT 0,
            lon           REAL    DEFAULT 0,
            plates_seen   TEXT    DEFAULT '',
            evidence_path TEXT    DEFAULT '',
            alert_sent    INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn


# Module-level connection (opened once)
_conn: sqlite3.Connection = None

def get_db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = _get_connection()
    return _conn


def log_plate(plate_text: str, confidence: float, incident_type: str = "None",
              image_path: str = "", lat: float = 0.0, lon: float = 0.0) -> int:
    """Insert a confirmed plate read into the DB. Returns row id."""
    ts = datetime.now().isoformat(timespec='seconds')
    try:
        cur = get_db().execute(
            "INSERT INTO vehicles (timestamp, plate_text, confidence, incident_type, image_path, lat, lon) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ts, plate_text.upper(), round(confidence, 3), incident_type, image_path, lat, lon)
        )
        get_db().commit()
        logging.info(f"[ANPR] Logged plate: {plate_text} ({confidence:.0%}) — {incident_type}")
        return cur.lastrowid
    except Exception as e:
        logging.error(f"[ANPR] DB write error: {e}")
        return -1


def log_incident(incident_type: str, severity: str, lat: float, lon: float,
                 plates_seen: list, evidence_path: str = "", alert_sent: bool = False) -> int:
    """Insert a confirmed incident (accident/fire) into the DB."""
    ts = datetime.now().isoformat(timespec='seconds')
    plates_str = ",".join(plates_seen)
    try:
        cur = get_db().execute(
            "INSERT INTO incidents (timestamp, incident_type, severity, lat, lon, plates_seen, evidence_path, alert_sent) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (ts, incident_type, severity, lat, lon, plates_str, evidence_path, int(alert_sent))
        )
        get_db().commit()
        return cur.lastrowid
    except Exception as e:
        logging.error(f"[ANPR] Incident DB write error: {e}")
        return -1


# ---------------------------------------------------------------------------
# OCR pipeline
# ---------------------------------------------------------------------------

def _get_reader():
    """Lazy-load EasyOCR reader (downloads model on first call ~200MB)."""
    global _READER
    if _READER is None:
        import easyocr
        print("[ANPR] Loading EasyOCR model (first run may take ~30s)...")
        _READER = easyocr.Reader(['en'], gpu=False, verbose=False)
        print("[ANPR] EasyOCR model ready.")
    return _READER


def _preprocess_crop(crop) -> list:
    """
    Return multiple preprocessed versions of the crop to maximise OCR hits.
    Strategies: raw resize, grayscale+CLAHE, Otsu threshold, sharpened.
    """
    h, w = crop.shape[:2]
    # Upscale small crops — OCR works best on larger images
    scale = max(1, 200 // max(h, 1))
    resized = cv2.resize(crop, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    enhanced = clahe.apply(gray)

    _, otsu = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(otsu, kernel, iterations=1)

    return [resized, cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR),
            cv2.cvtColor(otsu, cv2.COLOR_GRAY2BGR),
            cv2.cvtColor(dilated, cv2.COLOR_GRAY2BGR)]


def _match_plate(raw_text: str) -> str | None:
    """Clean OCR text and try to match Indian plate patterns."""
    # Normalise: uppercase, remove spaces/dashes, fix common OCR mistakes
    text = raw_text.upper().replace(" ", "").replace("-", "")
    text = text.replace("O", "0").replace("I", "1").replace("Q", "0")

    for pattern in PLATE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None


def read_plate_from_crop(crop) -> tuple[str | None, float]:
    """
    Main entry point. Given a BGR vehicle crop, returns (plate_text, confidence).
    Returns (None, 0.0) if no plate found or ANPR is disabled.
    """
    if not ANPR_AVAILABLE or crop is None or crop.size == 0:
        return None, 0.0

    # Skip crops that are too small to contain a readable plate
    h, w = crop.shape[:2]
    if h < 10 or w < 20:
        return None, 0.0

    try:
        reader = _get_reader()
        variants = _preprocess_crop(crop)
        best_plate, best_conf = None, 0.0

        for img in variants:
            results = reader.readtext(img, detail=1, paragraph=False)
            for (_, text, conf) in results:
                plate = _match_plate(text)
                if plate and conf > best_conf:
                    best_plate = plate
                    best_conf = conf

        return best_plate, best_conf

    except Exception as e:
        logging.warning(f"[ANPR] OCR error: {e}")
        return None, 0.0


# ---------------------------------------------------------------------------
# Analytics queries (used by /analytics and /anpr-log endpoints)
# ---------------------------------------------------------------------------

def get_recent_plates(limit: int = 50) -> list[dict]:
    """Return the most recent plate reads as a list of dicts."""
    try:
        cur = get_db().execute(
            "SELECT id, timestamp, plate_text, confidence, incident_type, image_path "
            "FROM vehicles ORDER BY id DESC LIMIT ?", (limit,)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    except Exception:
        return []


def get_plate_stats() -> dict:
    """Summary stats for the analytics dashboard."""
    try:
        db = get_db()
        total = db.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
        unique = db.execute("SELECT COUNT(DISTINCT plate_text) FROM vehicles").fetchone()[0]
        incident_plates = db.execute(
            "SELECT COUNT(*) FROM vehicles WHERE incident_type != 'None'"
        ).fetchone()[0]
        top_plates = db.execute(
            "SELECT plate_text, COUNT(*) as cnt FROM vehicles "
            "GROUP BY plate_text ORDER BY cnt DESC LIMIT 5"
        ).fetchall()
        return {
            "total_reads": total,
            "unique_plates": unique,
            "incident_plates": incident_plates,
            "top_plates": [{"plate": r[0], "count": r[1]} for r in top_plates],
        }
    except Exception:
        return {"total_reads": 0, "unique_plates": 0, "incident_plates": 0, "top_plates": []}
