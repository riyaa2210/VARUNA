# ===================================================================================
# main.py: UPGRADED - AI Accident Detection & Smart Traffic Control Backend
#
# NEW FEATURES:
# - Multi-junction support (2-6 way intersections)
# - Advanced accident response algorithms
# - Real-time algorithm visualization for dashboard
# ===================================================================================

import cv2
import asyncio
import uvicorn
import base64
import time
import os
import logging
import requests
import threading
import random
from datetime import datetime
from collections import deque, Counter
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Attempt to load local .env file (optional). If python-dotenv isn't installed,
# this will be silently ignored and environment variables must be set externally.
try:
    from dotenv import load_dotenv
    dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
except Exception:
    pass

# Import YOLO with graceful fallback
try:
    from ultralytics import YOLO
except ImportError:
    print("WARNING: ultralytics not found. YOLO detection will be disabled.")
    YOLO = None

# Import the new smart controller
try:
    from signal_algorithms import SmartSignalController, JunctionType, IncidentLevel
except ImportError:
    print("WARNING: signal_algorithms not found. Using basic signal control.")
    SmartSignalController = None

# --- Configuration ---
# OPTION 1: Live Camera (IP Stream) - ACTIVE
# Default path for Android IP Webcam / OWLRP stream
MOBILE_CAMERA_URL = os.getenv("MOBILE_CAMERA_URL", "https://192.168.0.125:8080")

# OPTION 2: Webcam (Use 0 for default webcam)
# MOBILE_CAMERA_URL = 0

# OPTION 3: Video File
# MOBILE_CAMERA_URL = os.path.join(os.path.dirname(__file__), "video.mp4")

# FORCE_MOBILE_CAMERA: If True, do NOT fall back to local webcam if IP camera fails
FORCE_MOBILE_CAMERA = True


def normalize_camera_url(url):
    """Normalize mobile camera URL to include common stream endpoint."""
    if not isinstance(url, str):
        return url

    url = url.strip().rstrip("/")
    if url.startswith("http://") or url.startswith("https://"):
        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(url)
        if parsed.path in ("", "/"):
            # Many IP Webcam apps expose the MJPEG endpoint at /video
            url = urlunparse(parsed._replace(path="/video"))
    return url

# Corrected model path - use absolute path
MODEL_NAME = os.path.join(os.path.dirname(__file__), 'backend', 'models', 'accident_v2.pt')

# --- Secrets (use environment variables; do NOT hardcode tokens) ---
# Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in your environment instead of
# committing them into source control. The app will fall back to empty strings
# if the environment variables are not set.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# --- Location Data ---
CAMERA_LAT = 15.4589
CAMERA_LON = 75.0078

# --- Detection Tuning ---
HISTORY_LEN = 12
SNAPSHOT_COOLDOWN = 5
MIN_CONF = 0.25

# --- Demo Failsafes ---
DEMO_ACCIDENT_MAP = ["motorcycle", "suitcase", "backpack", "handbag"]

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- Global State ---
manual_lane_data = {"east": 10, "south": 5, "west": 8}
incident_lock = False
last_snapshot_time = 0
current_algorithm = "adaptive"  # Can be changed via API

# --- NEW: Smart Signal Controller ---
# Initialize with 4-way junction (can be changed via API)
signal_controller = SmartSignalController(JunctionType.FOUR_WAY, current_algorithm) if SmartSignalController else None

# --- Model initialization (will be loaded asynchronously on startup) ---
model = None

# --- Continuous Scanning State ---
last_alert_timers = {"Accident": 0, "Fire": 0}
ALERT_INTERVAL = 30

# --- File System Setup ---
EVIDENCE_DIR = "evidence_archive"
os.makedirs(os.path.join(EVIDENCE_DIR, "minor"), exist_ok=True)
os.makedirs(os.path.join(EVIDENCE_DIR, "severe"), exist_ok=True)
os.makedirs(os.path.join(EVIDENCE_DIR, "fire"), exist_ok=True)


class VideoStream:
    def __init__(self, src=0):
        self.stream_src = src
        self.stream = None
        self.grabbed = False
        self.frame = None
        self.stopped = False
        self.thread = None
        self.use_http = False  # Flag for HTTP-based IP camera
        self.session = None

        try:
            if isinstance(src, str) and src.isnumeric():
                src = int(src)

            if isinstance(src, str):
                src = normalize_camera_url(src)

            # Check if it's an IP camera URL
            if isinstance(src, str) and src.startswith(('http://', 'https://')):
                print(f"[CAMERA] Detected IP camera URL: {src}")
                self.stream_src = src
                self.use_http = True
                # Try to connect and grab first frame
                self._init_http_camera(src)
            else:
                # Local camera or video file
                print(f"[CAMERA] Initializing local camera/file: {src}")
                self.stream = cv2.VideoCapture(src)
                self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                if not self.stream.isOpened():
                    raise ValueError(f"Unable to open video source: {src}")
                self.grabbed, self.frame = self.stream.read()
                if not self.grabbed:
                    print(f"[WARNING] Could not grab initial frame from {src}.")
        except Exception as e:
            print(f"[CAMERA] CAMERA ERROR: {e}")
            self.stopped = True

    def _init_http_camera(self, url):
        """Initialize HTTP-based IP camera connection"""
        try:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry

            def attempt_url(test_url):
                print(f"[CAMERA] Testing connection to {test_url}...")
                try:
                    resp = self.session.get(test_url, stream=True, timeout=1)
                    if resp.status_code == 200:
                        print(f"[CAMERA] ✓ Connected to IP camera successfully ({test_url})!")
                        self.stream_src = test_url
                        self._grab_http_frame(test_url)
                        return True
                except Exception as e:
                    print(f"[CAMERA] Probe failed for {test_url}: {e}")
                return False
            
            # Create session with retries (reduced for faster failure)
            self.session = requests.Session()
            self.session.verify = False  # Allow self-signed certs from IP Webcam
            retry = Retry(connect=1, backoff_factor=0.2)
            adapter = HTTPAdapter(max_retries=retry)
            self.session.mount('http://', adapter)
            self.session.mount('https://', adapter)
            # Suppress SSL warnings for self-signed certs
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            # Prefer single-frame JPEG endpoints first (many phone webcam apps expose /shot.jpg)
            candidate_urls = []
            parsed = None
            try:
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(url)
            except Exception:
                parsed = None

            # host root (scheme + netloc) - e.g. http://172.16.11.183:8080
            if parsed and parsed.netloc:
                root = parsed.scheme + '://' + parsed.netloc
            else:
                root = url.rstrip('/')

            print(f"[CAMERA] Attempting to connect to IP camera at: {root}")
            
            # Build candidates - PRIORITIZE continuous video streams over snapshots
            # Video streams (MJPEG) provide continuous frames; snapshots may be blank
            candidate_urls.extend([
                url,  # Try exact URL first (usually /video from config)
                root + '/video',      # MJPEG streaming endpoint
                root + '/mjpeg',      # Alternative MJPEG endpoint
                root + '/stream',     # Some cameras use /stream
                root + '/shot.jpg',   # JPEG snapshots (last resort)
            ])

            # If original URL had a path, keep those variants too
            if parsed and parsed.path and parsed.path != '/':
                base = url.rstrip('/')
                candidate_urls.extend([
                    base + '/mjpeg',
                    base + '/shot.jpg',
                ])

            # Remove duplicates while preserving order
            seen = set()
            unique_urls = [x for x in candidate_urls if not (x in seen or seen.add(x))]

            print(f"[CAMERA] Trying {len(unique_urls)} endpoint candidates...")
            for test_url in unique_urls:
                try:
                    # Quick probe to check content type without downloading full stream
                    probe = self.session.get(test_url, stream=True, timeout=1)
                    ctype = probe.headers.get('Content-Type', '')
                    probe.close()

                    print(f"[CAMERA] Response from {test_url}: Content-Type={ctype}")

                    # If endpoint returns an image (single JPEG), accept it immediately
                    if 'image' in ctype.lower():
                        if attempt_url(test_url):
                            return

                    # If endpoint looks like multipart/x-mixed-replace (mjpeg), accept it
                    if 'multipart' in ctype.lower() or 'mjpeg' in ctype.lower():
                        if attempt_url(test_url):
                            return

                    # Otherwise try the URL but treat failures as non-fatal
                    if attempt_url(test_url):
                        return
                except Exception as inner_e:
                    print(f"[CAMERA] Connection attempt failed for {test_url}: {inner_e}")

            print(f"[CAMERA] ✗ All camera URL candidates failed: {', '.join(unique_urls)}")
            print(f"[CAMERA] TROUBLESHOOTING:")
            print(f"  1. Check if phone is on same network as laptop")
            print(f"  2. Verify camera app is running on phone")
            print(f"  3. Confirm IP address: {root}")
            print(f"  4. Try connecting manually: http://{parsed.netloc if parsed else 'your_ip:8080'}/video")
            
            if FORCE_MOBILE_CAMERA:
                print(f"[CAMERA] ⚠️  FORCE_MOBILE_CAMERA is enabled - NOT falling back to local webcam!")
                print(f"[CAMERA] Fix the mobile camera connection and restart.")
                self.stopped = True
                return
            else:
                print(f"[CAMERA] Falling back to local webcam...")
                self._fallback_to_local_webcam()
            return

        except Exception as e:
            print(f"[CAMERA] ✗ Failed to connect to IP camera: {e}")
            if FORCE_MOBILE_CAMERA:
                print(f"[CAMERA] ⚠️  FORCE_MOBILE_CAMERA is enabled - NOT falling back to local webcam!")
                print(f"[CAMERA] Fix the mobile camera connection and restart.")
                self.stopped = True
                return
            else:
                print(f"[CAMERA] Falling back to local webcam...")
                self._fallback_to_local_webcam()
    
    def _fallback_to_local_webcam(self):
        """Fall back to local webcam if IP camera fails"""
        try:
            print(f"[CAMERA] Attempting to use local webcam (camera index 0)...")
            self.stream = cv2.VideoCapture(0)
            self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if self.stream.isOpened():
                self.grabbed, self.frame = self.stream.read()
                if self.grabbed:
                    print(f"[CAMERA] ✓ Local webcam initialized successfully!")
                    self.use_http = False
                    return
            print(f"[CAMERA] ✗ Local webcam also unavailable")
            self.stopped = True
        except Exception as e:
            print(f"[CAMERA] ✗ Failed to fallback to local webcam: {e}")
            self.stopped = True

    def _grab_http_frame(self, url):
        """Grab a frame from HTTP/MJPEG stream"""
        try:
            resp = self.session.get(url, stream=True, timeout=1)
            if resp.status_code != 200:
                self.grabbed = False
                return

            ctype = resp.headers.get('Content-Type', '').lower()

            # If this is a multipart MJPEG stream, parse JPEG frames from the stream
            if 'multipart' in ctype or 'mjpeg' in ctype:
                buffer = b''
                for chunk in resp.iter_content(chunk_size=4096):
                    if not chunk:
                        continue
                    buffer += chunk
                    # Search for JPEG start/end markers
                    start = buffer.find(b'\xff\xd8')
                    end = buffer.find(b'\xff\xd9')
                    if start != -1 and end != -1 and end > start:
                        frame_data = buffer[start:end+2]
                        buffer = buffer[end+2:]
                        import numpy as np
                        nparr = np.frombuffer(frame_data, np.uint8)
                        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        if img is not None:
                            self.frame = img
                            self.grabbed = True
                            return

                # If loop exits without extracting a frame
                self.grabbed = False
                return

            # Otherwise treat as a single-image endpoint (JPEG)
            frame_data = b''
            for chunk in resp.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                frame_data += chunk
                # small safety limit
                if len(frame_data) > 5_000_000:
                    break

            import numpy as np
            nparr = np.frombuffer(frame_data, np.uint8)
            self.frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            self.grabbed = self.frame is not None
        except Exception as e:
            print(f"[CAMERA] Error grabbing HTTP frame: {e}")
            self.grabbed = False

    def start(self):
        if self.stopped:
            return self
        self.thread = threading.Thread(target=self.update, args=(), daemon=True)
        self.thread.start()
        return self

    def update(self):
        while not self.stopped:
            try:
                if self.use_http:
                    # HTTP-based IP camera
                    self._grab_http_frame(self.stream_src)
                    if not self.grabbed:
                        print("[STREAM] Failed to grab frame. Reconnecting...")
                        time.sleep(2)
                else:
                    # cv2.VideoCapture based
                    if not self.stream or not self.stream.isOpened():
                        print("[STREAM] Stream is not open. Attempting to reconnect...")
                        if self.stream:
                            self.stream.release()
                        time.sleep(2)
                        self.stream = cv2.VideoCapture(self.stream_src)
                        if not self.stream.isOpened():
                            print("[ERROR] Reconnect failed. Stopping stream.")
                            self.stopped = True
                            break
                        else:
                            print("[OK] Stream reconnected.")
                            continue

                    grabbed, frame = self.stream.read()
                    if not grabbed:
                        # If it is a video file, it might have just ended.
                        if self.stream.get(cv2.CAP_PROP_POS_FRAMES) == self.stream.get(cv2.CAP_PROP_FRAME_COUNT):
                            print("[INFO] End of video file. Restarting from beginning...")
                            self.stream.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            continue
                        continue

                    self.grabbed, self.frame = grabbed, frame
            except Exception as e:
                print(f"[STREAM] Error in update loop: {e}")
                time.sleep(2)

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        if self.thread is not None:
            self.thread.join()
        if self.use_http and self.session:
            self.session.close()
        elif self.stream is not None and self.stream.isOpened():
            self.stream.release()

class Stabilizer:
    def __init__(self, history_length=15):
        self.history = deque(maxlen=history_length)

    def add(self, status):
        self.history.append(status)
        counts = Counter(self.history)
        most_common_status, count = counts.most_common(1)[0]
        threshold = len(self.history) * 0.6

        if most_common_status in ["Accident", "Fire"] and count > threshold:
            return most_common_status

        return "Normal"


status_stabilizer = Stabilizer(history_length=HISTORY_LEN)


def encode_frame(frame):
    """Encode frame to base64 for sending over websocket"""
    try:
        # Check if frame is too dark and automatically enhance it
        frame_mean = frame.mean()
        if frame_mean < 50:  # Frame is very dark
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) for enhancement
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            enhanced = cv2.merge([l, a, b])
            frame = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            print(f"[FRAME] Auto-enhanced dark frame (original mean={frame_mean:.1f})")
        
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{frame_base64}"
    except Exception as e:
        print(f"[ERROR] Failed to encode frame: {e}")
        return None

def handle_alert_background(level, title, message, frame_copy, status):
    print(f"🚀 [DEBUG] Attempting to send Telegram Alert: {title}")
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evidence_{timestamp}_{status}.jpg"
        subfolder = "fire" if status == "Fire" else "severe"
        filepath = os.path.join(EVIDENCE_DIR, subfolder, filename)
        cv2.imwrite(filepath, frame_copy)
        print(f"💾 [DEBUG] Image Saved: {filepath}")

        caption = f"🚨 *SIH ALERT: {title}*\nLevel: {level}\nInfo: {message}"
        url_photo = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        with open(filepath, "rb") as img_file:
            resp = requests.post(
                url_photo,
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": caption,
                    "parse_mode": "Markdown",
                },
                files={"photo": img_file},
            )
            print(f"📨 [DEBUG] Photo Response: {resp.status_code} {resp.text[:100]}")

        url_loc = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendLocation"
        requests.post(
            url_loc,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "latitude": CAMERA_LAT,
                "longitude": CAMERA_LON,
            },
        )
        logging.info("[BACKGROUND TASK] Alert Sent: " + title)
    except Exception as e:
        print(f"[ERROR] [TELEGRAM ERROR]: {e}")
        logging.error(f"[BACKGROUND ERROR] {e}")


# --- NEW: Smart Signal Decision Logic ---
def decide_signals_smart(north_ai_count: int) -> dict:
    """
    Uses the SmartSignalController algorithms instead of basic cycle logic.
    
    Returns: {'north': 'green', 'east': 'red', ...}
    """
    global signal_controller, manual_lane_data, current_algorithm
    
    if not signal_controller:
        return {}
        
    # Update the controller with latest traffic data
    traffic_data = {
        'north': north_ai_count,
        'east': manual_lane_data.get('east', 0),
        'south': manual_lane_data.get('south', 0),
        'west': manual_lane_data.get('west', 0)
    }
    signal_controller.update_traffic_data(traffic_data)

    # NEW: Apply selected algorithm
    if current_algorithm == "zone":
        # Force zone rotation (cycle through lanes)
        signal_controller.cycle_index += 1
    elif current_algorithm == "weighted":
        # Boost priority for high-traffic lanes
        for lane, count in traffic_data.items():
            if lane in signal_controller.lanes and count > 10:
                signal_controller.lanes[lane].priority = count * 2
    
    # Get optimized signals
    decision = signal_controller.decide_signals()
    
    # Convert Decision object to a simple dictionary for the payload
    signal_status = {lane: "red" for lane in signal_controller.lanes}
    if decision and decision.green_lane:
        signal_status[decision.green_lane] = "green"

    return signal_status


# --- ACCURACY FILTER ---
def is_valid_detection(name, conf, box_width, box_height):
    if name == "fire":
        if conf < 0.60:
            return False
        if box_width < 20 or box_height < 20:
            return False

    if name == "accident":
        if conf < 0.50:
            return False

    if name in ["car", "truck", "bus", "motorcycle"]:
        if conf < 0.30:
            return False

    return True


async def analyze_detections(results, model_names, frame):
    global last_snapshot_time, manual_lane_data, incident_lock, signal_controller

    snapshot_frame = None
    detected_objects = []
    max_conf = 0.0

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            name = model_names[cls_id]
            conf = float(box.conf[0])

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            width = x2 - x1
            height = y2 - y1

            if not is_valid_detection(name, conf, width, height):
                continue

            max_conf = max(max_conf, conf)

            if name in DEMO_ACCIDENT_MAP:
                name = "accident"
                conf = 0.99

            detected_objects.append(name)

            tid = int(box.id.item()) if box.id is not None else 0
            color = (
                (0, 0, 255)
                if name in ["accident", "fire", "severe_accident"]
                else (0, 255, 0)
            )
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame,
                f"#{tid} {name} {int(conf*100)}%",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )

    if len(detected_objects) > 0:
        # Save detected frames for archival evidence
        evidence_subdir = os.path.join(EVIDENCE_DIR, "detected")
        os.makedirs(evidence_subdir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        evidence_path = os.path.join(evidence_subdir, f"detected_{timestamp}.jpg")
        try:
            cv2.imwrite(evidence_path, frame)
            print(f"[EVIDENCE] Saved detected frame: {evidence_path}")
        except Exception as e:
            print(f"[EVIDENCE ERROR] Could not save detected frame: {e}")

        if any(x in ["fire", "accident"] for x in detected_objects):
            print(f"[ALERT] ALERT OBJECTS: {detected_objects}")

        if snapshot_frame is None:
            try:
                snapshot_frame = encode_frame(frame)
            except Exception as e:
                print(f"[EVIDENCE ERROR] Could not encode snapshot: {e}")

    print(f"[DETECT] ALL DETECTED: {detected_objects}")
    print(f"[DETECT] UNIQUE CLASSES: {set(detected_objects)}")

    VEHICLE_CLASSES = [
        "car", "truck", "bus", "vehicle",
        "motorcycle", "motorbike", "bike",
        "bicycle"
    ]
    
    ai_count = sum(
        1 for x in detected_objects 
        if x.lower() in [v.lower() for v in VEHICLE_CLASSES]
    )
    
    print(f"[VEHICLE] VEHICLE COUNT: {ai_count} (from {len(detected_objects)} total detections)")
    
    # --- Simplified signal logic ---
    sig_status = decide_signals_smart(ai_count)

    # Ensure all junction lanes are included
    if signal_controller:
        for lane_name in signal_controller.lanes.keys():
            if lane_name not in sig_status:
                sig_status[lane_name] = 'red'

    raw_stat = "Normal"
    if any(x in ["fire", "smoke"] for x in detected_objects):
        raw_stat = "Fire"
    elif any(x in ["accident", "severe_accident", "crash"] for x in detected_objects):
        raw_stat = "Accident"
    elif "minor_accident" in detected_objects:
        raw_stat = "Minor"
    elif ai_count > 4:
        raw_stat = "Traffic"

    stable_stat = status_stabilizer.add(raw_stat)
    current_time = time.time()

    if signal_controller:
        if stable_stat == "Fire":
            signal_controller.mark_incident('north', IncidentLevel.FIRE)
        elif stable_stat == "Accident":
            signal_controller.mark_incident('north', IncidentLevel.SEVERE_ACCIDENT)
        else:
            signal_controller.clear_incident('north')

    if stable_stat in ["Fire", "Accident"]:
        last_time = last_alert_timers.get(stable_stat, 0)
        if current_time - last_time > ALERT_INTERVAL:
            print(f"[FIRE] NEW INCIDENT DETECTED: {stable_stat}")
            last_alert_timers[stable_stat] = current_time
            incident_lock = True

            frame_to_save = frame.copy()
            t = threading.Thread(
                target=handle_alert_background,
                args=(
                    3 if stable_stat == "Fire" else 2,
                    f"{stable_stat.upper()} DETECTED",
                    f"Continuous Scan Mode. {stable_stat} spotted.",
                    frame_to_save,
                    stable_stat,
                ),
            )
            t.start()
            snapshot_frame = encode_frame(frame_to_save)

    elif stable_stat == "Normal" and incident_lock:
        if current_time - max(last_alert_timers.values(), default=0) > 10:
            incident_lock = False

    drift_lat = CAMERA_LAT + random.uniform(-0.00002, 0.00002)
    drift_lon = CAMERA_LON + random.uniform(-0.00002, 0.00002)

    timing_decision = signal_controller.decide_signals() if signal_controller else None
    green_lane = None
    time_remaining = 0

    if timing_decision and timing_decision.green_lane:
        green_lane = timing_decision.green_lane
        # Calculate time remaining based on cycle
        elapsed = time.time() - (signal_controller.last_switch_time or time.time())
        cycle_duration = signal_controller.EMERGENCY_CYCLE_TIME if incident_lock else signal_controller.BASE_CYCLE_TIME
        time_remaining = max(0, int(cycle_duration - elapsed))

    algorithm_info = {
        'active': 'Emergency Mode' if incident_lock else f'{current_algorithm.title()} Algorithm',
        'junction_type': f'{signal_controller.junction_type.value}-Way Intersection' if signal_controller else 'N/A',
        'incident_status': stable_stat,
        'algorithm': current_algorithm,
        'current_green_lane': green_lane,
        'time_remaining': time_remaining,
        'reason': timing_decision.reason if hasattr(timing_decision, 'reason') else 'Normal cycle'
    }

    payload = {
        "level": 0,
        "title": "SYSTEM NORMAL",
        "message": f"Traffic Normal. Count: {ai_count}",
        "color": "#4caf50",
        "corridor": False,
        "confidence": f"{int(max_conf*100)}%",
        "snapshot": snapshot_frame,
        "frame": encode_frame(frame),
        "car_count": ai_count,
        "signals": sig_status,
        "manual": manual_lane_data.copy(),
        "gps": [drift_lat, drift_lon],
        "incident_active": incident_lock,
        "algorithm": algorithm_info
    }

    if incident_lock:
        payload.update(
            {"level": 2, "title": "INCIDENT ACTIVE", "color": "red", "corridor": True}
        )
    elif stable_stat == "Traffic":
        payload.update({"level": 1, "title": "HEAVY TRAFFIC", "color": "orange"})

    return payload


app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


class LaneData(BaseModel):
    east: int
    south: int
    west: int


class JunctionConfig(BaseModel):
    """NEW: Allow changing junction type dynamically"""
    junction_type: int  # 2, 3, 4, 5, or 6


@app.post("/update-lanes")
async def update_lanes(d: LaneData):
    global manual_lane_data
    manual_lane_data = d.model_dump()
    return {"status": "ok"}


@app.post("/set-junction")
async def set_junction(config: JunctionConfig):
    """NEW: Change the junction configuration"""
    global signal_controller
    
    try:
        junction_type = JunctionType(config.junction_type)
        if signal_controller:
            signal_controller.change_junction(junction_type)
        else:
            signal_controller = SmartSignalController(junction_type)
        logging.info(f"[OK] Junction changed to: {junction_type.name}")
        return {"status": "ok", "junction": junction_type.name}
    except ValueError:
        return {"status": "error", "message": "Invalid junction type. Use 2-6."}


@app.post("/set-algorithm")
async def set_algorithm(algo: dict):
    """NEW: Change the active algorithm (adaptive, zone, weighted)"""
    global current_algorithm, signal_controller
    
    algo_name = algo.get("algorithm", "adaptive")
    valid_algos = ["adaptive", "zone", "weighted"]
    
    if algo_name not in valid_algos:
        return {"status": "error", "message": f"Must be one of {valid_algos}"}
    
    current_algorithm = algo_name
    if signal_controller:
        signal_controller.algorithm_mode = current_algorithm
    logging.info(f"Algorithm changed to: {current_algorithm}")
    return {"status": "ok", "algorithm": current_algorithm}


@app.post("/reset-system")
async def reset():
    global incident_lock, signal_controller
    incident_lock = False
    
    if signal_controller:
        for lane in signal_controller.lanes.keys():
            signal_controller.clear_incident(lane)
    
    print("[RESET] SYSTEM RESET")
    return {"status": "reset"}


@app.get("/health")
async def health_check():
    """Check if detection system is ready"""
    return {
        "status": "ok",
        "backend": "running",
        "yolo_model_loaded": model is not None,
        "model_path": MODEL_NAME,
        "camera_url": MOBILE_CAMERA_URL,
        "signal_controller_ready": signal_controller is not None
    }


@app.get("/test-camera")
async def test_camera():
    """Test camera connectivity"""
    print("[DEBUG] Testing camera connection...")
    
    test_vs = VideoStream(MOBILE_CAMERA_URL)
    
    if test_vs.stopped:
        print("[ERROR] Camera test failed - stream stopped")
        return {
            "status": "error",
            "camera_url": MOBILE_CAMERA_URL,
            "message": f"Failed to connect to {MOBILE_CAMERA_URL}. Check if camera is accessible.",
            "suggestions": [
                "1. Verify phone camera app is running",
                "2. Check both devices are on same WiFi network",
                "3. Try alternative endpoints: /stream, /mjpeg, or port 8081",
                "4. Use fallback: camera index 0 (local webcam)"
            ]
        }
    
    # Try to grab a frame
    test_vs.start()
    await asyncio.sleep(1)
    
    frame = test_vs.read()
    test_vs.stop()
    
    if frame is None:
        return {
            "status": "error",
            "camera_url": MOBILE_CAMERA_URL,
            "message": "Connected but couldn't grab frame"
        }
    
    return {
        "status": "ok",
        "camera_url": MOBILE_CAMERA_URL,
        "message": "Camera connection successful!",
        "frame_shape": frame.shape
    }


# --- ASYNC STARTUP EVENT FOR MODEL LOADING ---
@app.on_event("startup")
async def load_model_on_startup():
    """Load YOLO model asynchronously without blocking server startup"""
    global model
    
    print("[LOADING] LOADING MODEL...")
    print(f"[DEBUG] Model path: {MODEL_NAME}")
    print(f"[DEBUG] Model exists: {os.path.exists(MODEL_NAME)}")

    model = None
    if YOLO is not None:
        try:
            if not os.path.exists(MODEL_NAME):
                raise FileNotFoundError(f"Model file not found at {MODEL_NAME}")
            print(f"[DEBUG] Attempting to load model from {MODEL_NAME}...")
            model = await asyncio.to_thread(YOLO, MODEL_NAME)
            print("[✅ OK] CUSTOM MODEL LOADED SUCCESSFULLY!")
            print(f"[DEBUG] Model details: {model.names}")
        except Exception as e:
            print(f"[❌ WARNING] CUSTOM MODEL ERROR: {e}")
            print("[INFO] Attempting fallback to yolov8n.pt...")
            try:
                model = await asyncio.to_thread(YOLO, "yolov8n.pt")
                print("[✅ OK] FALLBACK MODEL LOADED")
            except Exception as e2:
                print(f"[❌ WARNING] FALLBACK MODEL ERROR: {e2}")
                print("[❌ WARNING] Running WITHOUT YOLO detection")
                model = None
    else:
        print("[❌ WARNING] ultralytics not installed. Running without YOLO detection support")


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[OK] FRONTEND CONNECTED")
    
    print(f"[CAMERA] ATTEMPTING CONNECTION TO: {MOBILE_CAMERA_URL}")
    vs = VideoStream(MOBILE_CAMERA_URL).start()
    
    if vs.stopped:
        print("[ERROR] CAMERA ERROR: VideoStream failed to initialize. Check URL or device.")
        try:
            await websocket.send_json({"error": "Failed to connect to video source."})
        except:
            pass
        await websocket.close()
        return

    time.sleep(2.0)
    frame_count = 0
    blank_frame_warnings = 0
    last_frame_log = 0

    try:
        while True:
            try:
                frame = vs.read()
                if frame is None:
                    if vs.stopped:
                        print("Video stream stopped. Closing websocket.")
                        break
                    await asyncio.sleep(0.05)
                    continue

                frame_count += 1
                
                # Check if frame is blank (all black or mostly uniform color)
                if frame.size > 0:
                    frame_mean = frame.mean()
                    frame_std = frame.std()
                    
                    # Log frame stats occasionally
                    current_time = time.time()
                    if current_time - last_frame_log > 5:  # Log every 5 seconds
                        print(f"[FRAME] Stats: mean={frame_mean:.1f}, std={frame_std:.1f}, shape={frame.shape}")
                        last_frame_log = current_time
                    
                    # Warn if frame appears blank (very low std or very dark)
                    if frame_std < 5 or frame_mean < 10:
                        blank_frame_warnings += 1
                        if blank_frame_warnings % 50 == 1:
                            print(f"[WARNING] Frame appears blank ({blank_frame_warnings} times). Check camera or stream endpoint.")
                else:
                    blank_frame_warnings += 1
                    print("[WARNING] Frame buffer is empty!")
                    await asyncio.sleep(0.1)
                    continue

                frame = cv2.resize(frame, (640, 480))
                frame_base64 = encode_frame(frame)
                
                # Prepare frame for YOLO - enhance if dark
                detection_frame = frame.copy()
                frame_mean = detection_frame.mean()
                if frame_mean < 50:
                    lab = cv2.cvtColor(detection_frame, cv2.COLOR_BGR2LAB)
                    l, a, b = cv2.split(lab)
                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                    l = clahe.apply(l)
                    detection_frame = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
                
                if model is not None:
                    try:
                        results = await asyncio.to_thread(
                            model.track, detection_frame, conf=0.15, persist=True, verbose=False
                        )
                        data = await analyze_detections(results, model.names, frame)
                    except Exception as e:
                        print(f"[YOLO ERROR] {e}")
                        sig_status = decide_signals_smart(0)
                        data = {
                            "signals": sig_status,
                            "status": "Processing Error",
                            "vehicle_count": 0,
                        }
                else:
                    sig_status = decide_signals_smart(0)
                    data = {
                        "signals": sig_status,
                        "status": "Normal",
                        "vehicle_count": 0,
                        "detections": [],
                        "junction": "4-way",
                        "timestamp": datetime.now().isoformat(),
                        "location": {"lat": CAMERA_LAT, "lon": CAMERA_LON},
                    }
                
                # Always include the frame for display
                data["frame"] = frame_base64

                # Keep snapshot if provided (detection can include this)
                # do not overwrite from include->None for normal frames
                if "snapshot" not in data:
                    data["snapshot"] = None

                await websocket.send_json(data)
                await asyncio.sleep(0.02)  # Minimal delay
                
            except WebSocketDisconnect:
                print("[ERROR] FRONTEND DISCONNECTED")
                break
            except asyncio.CancelledError:
                print("[WARNING] WebSocket task cancelled")
                break
            except Exception as e:
                print(f"[FRAME ERROR] {e}")
                await asyncio.sleep(0.05)
                continue

    except Exception as e:
        print(f"[CRASH] UNEXPECTED ERROR in websocket loop: {e}")
    finally:
        vs.stop()
        print("🛑 Video stream stopped.")
        try:
            if websocket.client_state != 3:  # 3 is 'DISCONNECTED'
                await websocket.close()
        except Exception:
            pass



# --- MOUNT STATIC DASHBOARD FILES LAST (after all API routes) ---
build_path = os.path.join(os.path.dirname(__file__), "dashboard", "build")
if os.path.exists(build_path):
    print(f"[OK] Serving React dashboard from: {build_path}")
    app.mount("/", StaticFiles(directory=build_path, html=True), name="dashboard")
else:
    print(f"[ERROR] Build directory not found: {build_path}")
    print("[ERROR] Dashboard will NOT be available. Run: npm run build in dashboard folder")


if __name__ == "__main__":
    print("===================================================")
    print("  🚦 AI TRAFFIC & INCIDENT MANAGEMENT SYSTEM 🚦")
    print("===================================================")

    web_host = os.getenv("WEB_HOST", "0.0.0.0")
    web_port = int(os.getenv("WEB_PORT", "8000"))
    print(f"[SERVER] Starting on {web_host}:{web_port} (use http://<YOUR_PC_IP>:{web_port} from phone)")
    # Using port 8000 to match dashboard and start_system.py expectations
    uvicorn.run(app, host=web_host, port=web_port)
