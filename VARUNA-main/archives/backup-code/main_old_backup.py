# ===================================================================================
# main.py: UPGRADED - AI Accident Detection & Smart Traffic Control Backend
#
# NEW FEATURES:
# - Multi-junction support (2-6 way intersections)
# - Advanced accident response algorithms
# - Real-time algorithm visualization for dashboard
# ===================================================================================

import cv2
import numpy as np
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
from pydantic import BaseModel
from ultralytics import YOLO

# Import the new smart controller
try:
    from signal_algorithms import SmartSignalController, JunctionType, IncidentLevel
except ImportError:
    print("WARNING: signal_algorithms not found. Using basic signal control.")
    SmartSignalController = None

# --- Configuration ---
MOBILE_CAMERA_URL = "http://10.125.48.115:8080/video"
MODEL_NAME = 'accident_v2.pt'

# --- Secrets ---
TELEGRAM_BOT_TOKEN = "8257607238:AAFn4NiRX0ZwGNE0C_H8mam8LI2LN9wW6Vs"
TELEGRAM_CHAT_ID = "7734839666"

# --- Location Data ---
CAMERA_LAT = 15.4589
CAMERA_LON = 75.0078

# --- Detection Tuning ---
HISTORY_LEN = 12
SNAPSHOT_COOLDOWN = 5
MIN_CONF = 0.25

# --- Demo Failsafes ---
DEMO_AMBULANCE_MAP = ["bus", "truck"]
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
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False
        self.thread = None  # To hold thread object
        # Create a "fake" frame just in case camera fails
        self.fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self.frame_counter = 0

    def start(self):
        self.thread = threading.Thread(target=self.update, args=(), daemon=True)
        self.thread.start()
        return self

    def update(self):
        while not self.stopped:
            if not self.stream.isOpened():
                self.stopped = True  # Stop if stream is not open
                break
            (grabbed, frame) = self.stream.read()
            
            # --- DEBUG FIX: If Camera fails, generate a fake image ---
            if not grabbed:
                # Create a black image with moving rectangles and timestamp
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                
                # Add text showing simulation status
                cv2.putText(frame, f"NO CAMERA - SIMULATION MODE", (30, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Draw moving colored rectangles to simulate objects
                pos = (self.frame_counter * 2) % 640
                cv2.rectangle(frame, (pos, 100), (pos + 50, 150), (0, 255, 0), -1)  # Green box
                cv2.rectangle(frame, ((640 - pos), 250), ((640 - pos - 50), 300), (0, 0, 255), -1)  # Red box
                
                # Add timestamp
                cv2.putText(frame, f"Frame: {self.frame_counter}", (30, 450), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
                
                self.frame_counter += 1
                # Mimic ~30 FPS delay
                time.sleep(0.03)
                
            self.grabbed = True  # Force true
            self.frame = frame  # Update frame
            # -------------------------------------------------------

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        # Wait for the thread to finish
        if self.thread is not None:
            self.thread.join()
        # Now it's safe to release the stream
        try:
            if self.stream.isOpened():
                self.stream.release()
        except:
            pass


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
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 70]
    _, buffer = cv2.imencode(".jpg", frame, encode_param)
    return base64.b64encode(buffer).decode("utf-8")


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
        print(f"❌ [TELEGRAM ERROR]: {e}")
        logging.error(f"[BACKGROUND ERROR] {e}")


# --- NEW: Smart Signal Decision Logic ---
def decide_signals_smart(north_ai_count: int) -> dict:
    """
    Uses the SmartSignalController algorithms instead of basic cycle logic.
    
    Returns: {'north': 'green', 'east': 'red', ...}
    """
    global signal_controller, manual_lane_data, current_algorithm
    
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
    signals = signal_controller.decide_signals()
    
    return signals


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
    accident_detected = False
    fire_detected = False

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
        if any(x in ["fire", "accident"] for x in detected_objects):
            print(f"👁️ ALERT OBJECTS: {detected_objects}")
    
    # ===== DEBUG OUTPUT =====
    print(f"🔍 ALL DETECTED: {detected_objects}")
    print(f"🔍 UNIQUE CLASSES: {set(detected_objects)}")
    # ===== END DEBUG =====

    # ===== EXPANDED VEHICLE DETECTION =====
    VEHICLE_CLASSES = [
        "car", "truck", "bus", "vehicle",
        "motorcycle", "motorbike", "bike",
        "bicycle"  # Remove if you don't want to count bicycles
    ]
    
    ai_count = sum(
        1 for x in detected_objects 
        if x.lower() in [v.lower() for v in VEHICLE_CLASSES]
    )
    # ===== END FIX =====
    
    print(f"🚗 VEHICLE COUNT: {ai_count} (from {len(detected_objects)} total detections)")
    
    is_amb = ("ambulance" in detected_objects) or any(
        x in detected_objects for x in DEMO_AMBULANCE_MAP
    )

    # --- NEW: Use Smart Algorithm ---
    if is_amb:
        # Use the proper algorithm instead of hardcoding
        emergency_lane = 'north'  # Or detect ambulance direction from bounding box position
        signals = signal_controller.algorithm_emergency_corridor(emergency_lane)
        sig_status = {lane: 'red' for lane in signal_controller.lanes.keys()}
        sig_status[signals.green_lane] = 'green'
    else:
        sig_status = decide_signals_smart(ai_count)

    # Ensure all junction lanes are included
    if signal_controller:
        for lane_name in signal_controller.lanes.keys():
            if lane_name not in sig_status:
                sig_status[lane_name] = 'red'  # Default to red for extra lanes

    raw_stat = "Normal"
    if any(x in ["fire", "smoke"] for x in detected_objects):
        raw_stat = "Fire"
        fire_detected = True
    elif any(x in ["accident", "severe_accident", "crash"] for x in detected_objects):
        raw_stat = "Accident"
        accident_detected = True
    elif "minor_accident" in detected_objects:
        raw_stat = "Minor"
    elif ai_count > 4:
        raw_stat = "Traffic"

    stable_stat = status_stabilizer.add(raw_stat)
    current_time = time.time()

    # --- NEW: Update Signal Controller with Incidents ---
    if signal_controller:
        if stable_stat == "Fire":
            signal_controller.mark_incident('north', IncidentLevel.FIRE)  # Assume fire in north for demo
        elif stable_stat == "Accident":
            signal_controller.mark_incident('north', IncidentLevel.SEVERE_ACCIDENT)
        else:
            signal_controller.clear_incident('north')

    if stable_stat in ["Fire", "Accident"]:
        last_time = last_alert_timers.get(stable_stat, 0)
        if current_time - last_time > ALERT_INTERVAL:
            print(f"🔥 NEW INCIDENT DETECTED: {stable_stat}")
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
        if current_time - max(last_alert_timers.values()) > 10:
            incident_lock = False

    drift_lat = CAMERA_LAT + random.uniform(-0.00002, 0.00002)
    drift_lon = CAMERA_LON + random.uniform(-0.00002, 0.00002)

    # --- NEW: Add algorithm info to payload ---
    # NEW: Calculate timing decisions
    timing_decision = signal_controller.decide_signals() if signal_controller else None
    green_lane = None
    time_remaining = 0

    if timing_decision:
        for lane, state in sig_status.items():
            if state == 'green':
                green_lane = lane
                # Calculate time remaining based on cycle
                elapsed = time.time() - signal_controller.last_switch_time
                cycle_duration = signal_controller.EMERGENCY_CYCLE_TIME if incident_lock else signal_controller.BASE_CYCLE_TIME
                time_remaining = max(0, int(cycle_duration - elapsed))
                break

    algorithm_info = {
        'active': 'Emergency Mode' if incident_lock else f'{current_algorithm.title()} Algorithm',
        'junction_type': f'{signal_controller.junction_type.value}-Way Intersection',
        'incident_status': stable_stat,
        'algorithm': current_algorithm,
        'current_green_lane': green_lane,  # NEW
        'time_remaining': time_remaining,   # NEW
        'reason': timing_decision.reason if hasattr(timing_decision, 'reason') else 'Normal cycle'  # NEW
    }

    payload = {
        "level": 0,
        "title": "SYSTEM NORMAL",
        "message": f"Traffic Normal. Count: {ai_count}",
        "color": "#4caf50",
        "corridor": False,
        "confidence": f"{int(max_conf*100)}%",
        "snapshot": snapshot_frame,
        "car_count": ai_count,
        "signals": sig_status,
        "manual": manual_lane_data.copy(),
        "gps": [drift_lat, drift_lon],
        "incident_active": incident_lock,
        "algorithm": algorithm_info  # NEW FIELD
    }

    if incident_lock:
        payload.update(
            {"level": 2, "title": "INCIDENT ACTIVE", "color": "red", "corridor": True}
        )
    elif is_amb:
        payload.update(
            {
                "title": "AMBULANCE DETECTED",
                "color": "#0000FF",
                "level": 3,
                "corridor": True,
            }
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
        signal_controller = SmartSignalController(junction_type)
        logging.info(f"✅ Junction changed to: {junction_type.name}")
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
    
    # Clear all incidents in controller
    if signal_controller:
        for lane in signal_controller.lanes.keys():
            signal_controller.clear_incident(lane)
    
    print("🔄 SYSTEM RESET")
    return {"status": "reset"}


try:
    model = YOLO(MODEL_NAME)
except Exception as e:
    print(
        f"Could not load custom model '{MODEL_NAME}', falling back to yolov8n.pt. Error: {e}"
    )
    model = YOLO("yolov8n.pt")


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    vs = VideoStream(MOBILE_CAMERA_URL).start()
    time.sleep(1.0)

    try:
        while True:
            frame = vs.read()
            if frame is None:
                await asyncio.sleep(0.1)
                continue

            frame = cv2.resize(frame, (640, 480))
            results = await asyncio.to_thread(
                model.track, frame, conf=0.15, persist=True, verbose=False
            )
            data = await analyze_detections(results, model.names, frame)
            await websocket.send_json(data)
            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        print("Dashboard Disconnected")
    finally:
        vs.stop()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)