import cv2
import asyncio
import uvicorn
import base64
import time
import os
import logging
from datetime import datetime
from collections import deque, Counter
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ultralytics import YOLO
from twilio.rest import Client
import random

# --- CONFIGURATION ---
# ⚠️ YOUR IP ADDRESS
MOBILE_CAMERA_URL = "http://10.14.121.102:8080/video"
MODEL_NAME = 'accident_v2.pt'

# Twilio Configuration
TWILIO_SID = os.getenv("TWILIO_SID", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
TWILIO_FROM = os.getenv("TWILIO_FROM", "+15551234567")
TWILIO_TO_POLICE = os.getenv("TWILIO_TO_POLICE", "+919999999999")

# Runtime Tunables
HISTORY_LEN = 12       # Faster reaction time for demo
SNAPSHOT_COOLDOWN = 5 
SMS_COOLDOWN = 300
MIN_CONF = 0.40        # Lower confidence for demo conditions

# Demo helper: allow mapping other detected classes (e.g., 'bus') to act as 'ambulance'
# Set env var `DEMO_AMBULANCE_MAP` to a comma-separated list like "bus,truck" to enable
DEMO_AMBULANCE_MAP = [s.strip() for s in os.getenv("DEMO_AMBULANCE_MAP", "bus").split(',') if s.strip()]

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
last_sms_time = {}

# --- GLOBAL TRAFFIC STATE ---
# Stores counts for lanes controlled by sliders
manual_lane_data = {
    "east": 10,
    "south": 5,
    "west": 8
}

# Rotation / cycle globals for hybrid signal logic
last_cycle_switch = 0
current_cycle_index = 0
CYCLE_DURATION = 5  # Seconds to hold green in normal rotation
LANE_ORDER = ["north", "east", "south", "west"]

# --- SYSTEM SETUP ---
EVIDENCE_DIR = "evidence_archive"
os.makedirs(os.path.join(EVIDENCE_DIR, "minor"), exist_ok=True)
os.makedirs(os.path.join(EVIDENCE_DIR, "severe"), exist_ok=True)
os.makedirs(os.path.join(EVIDENCE_DIR, "fire"), exist_ok=True)

# --- HELPER CLASSES ---
class Stabilizer:
    def __init__(self, history_length=15):
        self.history = deque(maxlen=history_length)
    
    def add(self, status):
        self.history.append(status)
        counts = Counter(self.history)
        most_common_status, count = counts.most_common(1)[0]
        
        # Logic: 50% agreement required for smoother demo
        if most_common_status in ["Accident", "Fire", "Minor"]:
            if count > (self.history.maxlen * 0.5): 
                return most_common_status
            else:
                return "Normal"
        return most_common_status

status_stabilizer = Stabilizer(history_length=HISTORY_LEN)
last_snapshot_time = 0 

# --- UTILITIES ---
def encode_frame(frame):
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode('utf-8')

def save_evidence_to_disk(frame, status):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evidence_{timestamp}_{status}.jpg"
        
        if status == "Fire": subfolder = "fire"
        elif status == "Accident": subfolder = "severe"
        else: subfolder = "minor"
            
        filepath = os.path.join(EVIDENCE_DIR, subfolder, filename)
        cv2.imwrite(filepath, frame)
        print(f"[STORAGE] Evidence saved: {filepath}")
        return filepath
    except Exception as e:
        print(f"[ERROR] Failed to save evidence: {e}")
        return None

def send_sms_alert(level, message):
    global last_sms_time
    current_time = time.time()
    last_sent = last_sms_time.get(level)
    if last_sent and (current_time - last_sent) < SMS_COOLDOWN: return False

    if TWILIO_SID.startswith("AC") and "xxxx" not in TWILIO_SID:
        try:
            Client(TWILIO_SID, TWILIO_TOKEN).messages.create(
                body=f"SIH ALERT: {message}\nLevel: {level}",
                from_=TWILIO_FROM, to=TWILIO_TO_POLICE
            )
            logging.info(f"[SMS] Sent: {message}")
            last_sms_time[level] = current_time
            return True
        except: return False
    else:
        logging.info(f"[SMS SIMULATION] Msg: {message}")
        last_sms_time[level] = current_time
        return False

# --- SMART SIGNAL LOGIC ---
def decide_signals(north_ai_count):
    """
    Hybrid signal decision:
    - Priority Mode: If one lane is significantly heavier, give it green.
    - Round-Robin Mode: Otherwise rotate green every `CYCLE_DURATION` seconds.
    """
    global last_cycle_switch, current_cycle_index

    # 1. Get all counts
    all_lanes = {
        "north": north_ai_count,
        "east": manual_lane_data["east"],
        "south": manual_lane_data["south"],
        "west": manual_lane_data["west"]
    }

    # 2. Determine the busiest lane and totals
    max_lane = max(all_lanes, key=all_lanes.get)
    max_val = all_lanes[max_lane]
    total_traffic = sum(all_lanes.values())

    selected_green = ""

    # 3. SMART LOGIC: Is one lane significantly heavier?
    # Condition: The busiest lane must have ~30% more than the average (avoid division by zero)
    if total_traffic > 5 and max_val > (total_traffic / 4) * 1.3:
        selected_green = max_lane  # Priority Mode
    else:
        # 4. NORMAL LOGIC: Round Robin Cycle
        current_time = time.time()
        if current_time - last_cycle_switch > CYCLE_DURATION:
            current_cycle_index = (current_cycle_index + 1) % len(LANE_ORDER)
            last_cycle_switch = current_time
        selected_green = LANE_ORDER[current_cycle_index]

    # 5. Set Signals
    signals = {
        "north": "green" if selected_green == "north" else "red",
        "east": "green" if selected_green == "east" else "red",
        "south": "green" if selected_green == "south" else "red",
        "west": "green" if selected_green == "west" else "red"
    }
    return signals

# --- CORE LOGIC ---
def analyze_detections(results, model_names, frame):
    global last_snapshot_time
    detected_objects = []
    max_conf = 0.0
    snapshot_frame = frame.copy()
    
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            name = model_names[cls_id]
            conf = float(box.conf[0])
            detected_objects.append(name)
            if conf > max_conf: max_conf = conf
            
            # Visualization
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            color = (0, 0, 255) if "accident" in name or "fire" in name else (0, 255, 0)
            cv2.rectangle(snapshot_frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(snapshot_frame, f"{name} {int(conf*100)}%", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # 1. AI CAR COUNTING (NORTH LANE)
    ai_car_count = 0
    for obj in detected_objects:
        if obj in ['car', 'truck', 'bus', 'vehicle']:
            ai_car_count += 1
            
    # 2. RUN CENTRAL SIGNAL LOGIC
    # Emergency vehicle preemption: if ambulance detected, force green for North
    # For demo: allow other classes to be treated as ambulance via DEMO_AMBULANCE_MAP
    is_ambulance = ('ambulance' in detected_objects) or any(cls in detected_objects for cls in DEMO_AMBULANCE_MAP)
    if is_ambulance:
        signal_status = {"north": "green", "east": "red", "south": "red", "west": "red"}
    else:
        signal_status = decide_signals(ai_car_count)

    # Status Analysis
    raw_status = "Normal"
    if any(x in ['fire', 'smoke'] for x in detected_objects): raw_status = "Fire"
    elif any(x in ['severe_accident', 'accident', 'crash'] for x in detected_objects): raw_status = "Accident"
    elif 'minor_accident' in detected_objects: raw_status = "Minor"
    elif ai_car_count > 4: raw_status = "Traffic"

    stable_status = status_stabilizer.add(raw_status)
    
    snapshot_data = None
    current_time = time.time()
    
    if stable_status in ["Fire", "Accident", "Minor"] and (current_time - last_snapshot_time > SNAPSHOT_COOLDOWN):
        save_evidence_to_disk(snapshot_frame, stable_status)
        snapshot_data = encode_frame(snapshot_frame)
        last_snapshot_time = current_time

    # Build Payload
    alert_payload = {
        "level": 0,
        "title": "SYSTEM NORMAL",
        "message": f"Traffic Flow Normal. Vehicles: {ai_car_count}",
        "color": "#4caf50",
        "corridor": False,
        "confidence": f"{int(max_conf * 100)}%",
        "snapshot": snapshot_data,
        "car_count": ai_car_count,
        "signals": signal_status, # <--- Sending Decision to React
        "manual": manual_lane_data.copy()  # include manual lane state for frontend confirmation
    }

    if stable_status == "Fire":
        alert_payload.update({"level": 3, "title": "FIRE DETECTED", "color": "darkred", "corridor": True})
        send_sms_alert(3, "Fire Detected")
    elif stable_status == "Accident":
        alert_payload.update({"level": 2, "title": "SEVERE CRASH", "color": "red", "corridor": True})
        send_sms_alert(2, "Severe Crash")
    elif stable_status == "Traffic":
        alert_payload.update({"level": 1, "title": "HEAVY TRAFFIC", "color": "orange"})

    # If ambulance was detected, override alert to indicate emergency
    if is_ambulance:
        alert_payload.update({
            'title': 'AMBULANCE DETECTED',
            'color': '#0000FF',
            'level': 3,
            'corridor': True
        })
    
    return alert_payload

# --- SERVER INITIALIZATION ---
app = FastAPI()

# Allow React to send POST requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Model for Manual Inputs
class LaneUpdate(BaseModel):
    east: int
    south: int
    west: int

# API Endpoint to receive slider data
@app.post("/update-lanes")
async def update_lanes(data: LaneUpdate):
    global manual_lane_data
    manual_lane_data["east"] = data.east
    manual_lane_data["south"] = data.south
    manual_lane_data["west"] = data.west
    return {"status": "updated", "current": manual_lane_data}

# Load AI
try: model = YOLO(MODEL_NAME)
except: model = YOLO('yolov8n.pt')

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    cap = cv2.VideoCapture(MOBILE_CAMERA_URL)
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                await asyncio.sleep(2)
                cap = cv2.VideoCapture(MOBILE_CAMERA_URL)
                continue

            frame_count += 1
            if frame_count % 4 != 0: # Optimize speed
                await asyncio.sleep(0.01)
                continue 

            frame = cv2.resize(frame, (640, 480))
            
            # Run Async Inference
            results = await asyncio.to_thread(model, frame, conf=MIN_CONF, verbose=False)
            
            alert_data = analyze_detections(results, model.names, frame)
            await websocket.send_json(alert_data)
            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        print("Dashboard Disconnected")
    finally:
        cap.release()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)