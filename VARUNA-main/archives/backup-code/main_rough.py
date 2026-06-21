# ===================================================================================
# main.py: TRIPLE MODEL SYSTEM - HIGH ACCURACY VERSION
# Model 1: vehicle_detecting.pt - Vehicle counting (custom trained)
# Model 2: ambulance_detection.pt - Emergency vehicle detection
# Model 3: damage.pt - Accident severity classification
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
from pydantic import BaseModel
from ultralytics import YOLO

try:
    from signal_algorithms import SmartSignalController, JunctionType, IncidentLevel
except ImportError:
    print("WARNING: signal_algorithms not found. Using basic signal control.")
    SmartSignalController = None

# --- Configuration ---
MOBILE_CAMERA_URL = "http://10.125.48.115:8080/video"

# --- Secrets ---
TELEGRAM_BOT_TOKEN = "8257607238:AAFn4NiRX0ZwGNE0C_H8mam8LI2LN9wW6Vs"
TELEGRAM_CHAT_ID = "7734839666"

# --- Location Data ---
CAMERA_LAT = 15.4589
CAMERA_LON = 75.0078

# --- Detection Tuning ---
HISTORY_LEN = 12
SNAPSHOT_COOLDOWN = 5

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- Global State ---
manual_lane_data = {"east": 10, "south": 5, "west": 8}
incident_lock = False
last_snapshot_time = 0
current_algorithm = "adaptive"

signal_controller = SmartSignalController(JunctionType.FOUR_WAY, current_algorithm) if SmartSignalController else None

last_alert_timers = {"Accident": 0, "Fire": 0}
ALERT_INTERVAL = 30

# --- File System Setup ---
EVIDENCE_DIR = "evidence_archive"
os.makedirs(os.path.join(EVIDENCE_DIR, "minor"), exist_ok=True)
os.makedirs(os.path.join(EVIDENCE_DIR, "moderate"), exist_ok=True)
os.makedirs(os.path.join(EVIDENCE_DIR, "severe"), exist_ok=True)


class VideoStream:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self.update, args=(), daemon=True)
        self.thread.start()
        return self

    def update(self):
        while not self.stopped:
            if not self.stream.isOpened():
                self.stopped = True
                break
            (grabbed, frame) = self.stream.read()
            if not grabbed:
                self.stopped = True
                break
            self.grabbed, self.frame = grabbed, frame

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        if self.thread is not None:
            self.thread.join()
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
    print(f"🚀 [ALERT] Sending Telegram: {title}")
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evidence_{timestamp}_{status}.jpg"
        
        # Choose folder based on severity
        if status in ["severe", "Severe", "severe_damage"]:
            subfolder = "severe"
        elif status in ["moderate", "Moderate", "moderate_damage"]:
            subfolder = "moderate"
        else:
            subfolder = "minor"
            
        filepath = os.path.join(EVIDENCE_DIR, subfolder, filename)
        cv2.imwrite(filepath, frame_copy)
        print(f"💾 [SAVED] {filepath}")

        caption = f"🚨 *SIH ALERT: {title}*\nLevel: {level}\nSeverity: {status}\nLocation: {CAMERA_LAT}, {CAMERA_LON}"
        url_photo = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        
        with open(filepath, "rb") as img_file:
            resp = requests.post(
                url_photo,
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "Markdown"},
                files={"photo": img_file},
                timeout=10
            )
            print(f"📨 [TELEGRAM] Status: {resp.status_code}")

        url_loc = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendLocation"
        requests.post(
            url_loc,
            data={"chat_id": TELEGRAM_CHAT_ID, "latitude": CAMERA_LAT, "longitude": CAMERA_LON},
            timeout=5
        )
        
    except Exception as e:
        print(f"❌ [TELEGRAM ERROR]: {e}")


def decide_signals_smart(north_ai_count: int) -> dict:
    global signal_controller, manual_lane_data, current_algorithm
    
    traffic_data = {
        'north': north_ai_count,
        'east': manual_lane_data.get('east', 0),
        'south': manual_lane_data.get('south', 0),
        'west': manual_lane_data.get('west', 0)
    }
    signal_controller.update_traffic_data(traffic_data)

    if current_algorithm == "zone":
        signal_controller.cycle_index += 1
    elif current_algorithm == "weighted":
        for lane, count in traffic_data.items():
            if lane in signal_controller.lanes and count > 10:
                signal_controller.lanes[lane].priority = count * 2
    
    signals = signal_controller.decide_signals()
    return signals


def is_valid_detection(name, conf, box_width, box_height):
    """Validation filter for all models"""
    
    # Vehicle detection (from vehicle_detecting.pt)
    if name.lower() in ["car", "truck", "bus", "motorcycle", "vehicle", "bicycle"]:
        return conf > 0.20 and box_width > 15 and box_height > 15
    
    # Ambulance detection (from ambulance_detection.pt)
    if "ambulance" in name.lower():
        return conf > 0.30 and box_width > 30 and box_height > 30
    
    # Damage severity (from damage.pt)
    if any(x in name.lower() for x in ["damage", "minor", "moderate", "severe", "accident"]):
        return conf > 0.35 and box_width > 20 and box_height > 20
    
    return True


async def analyze_detections(vehicle_results, ambulance_results, damage_results, 
                            vehicle_names, ambulance_names, damage_names, frame):
    """
    Triple model analysis pipeline:
    1. Count vehicles from vehicle_detecting.pt
    2. Detect ambulances from ambulance_detection.pt
    3. Classify accident severity from damage.pt
    """
    global last_snapshot_time, manual_lane_data, incident_lock, signal_controller

    snapshot_frame = None
    detected_vehicles = []
    detected_ambulances = []
    detected_damage = []
    max_conf = 0.0
    highest_severity = "None"

    # ===== MODEL 1: VEHICLE COUNTING =====
    for r in vehicle_results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            name = vehicle_names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            width, height = x2 - x1, y2 - y1

            if not is_valid_detection(name, conf, width, height):
                continue

            max_conf = max(max_conf, conf)
            detected_vehicles.append(name)

            tid = int(box.id.item()) if box.id is not None else 0
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"#{tid} {name} {int(conf*100)}%", 
                       (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # ===== MODEL 2: AMBULANCE DETECTION =====
    for r in ambulance_results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            name = ambulance_names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            width, height = x2 - x1, y2 - y1

            if not is_valid_detection(name, conf, width, height):
                continue

            if "ambulance" in name.lower():
                detected_ambulances.append(name)
                
                # Draw special blue box for ambulance
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 3)
                cv2.putText(frame, f"🚑 AMBULANCE {int(conf*100)}%", 
                           (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    # ===== MODEL 3: DAMAGE SEVERITY =====
    for r in damage_results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            name = damage_names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            width, height = x2 - x1, y2 - y1

            if not is_valid_detection(name, conf, width, height):
                continue

            detected_damage.append(name)
            
            # Determine color based on severity
            if "severe" in name.lower():
                color = (0, 0, 255)  # Red
                highest_severity = "Severe"
            elif "moderate" in name.lower():
                color = (0, 165, 255)  # Orange
                if highest_severity != "Severe":
                    highest_severity = "Moderate"
            else:
                color = (0, 255, 255)  # Yellow
                if highest_severity == "None":
                    highest_severity = "Minor"
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            cv2.putText(frame, f"⚠️ {name.upper()} {int(conf*100)}%", 
                       (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # ===== CONSOLE DEBUG =====
    print(f"\n{'='*60}")
    print(f"🚗 VEHICLES: {detected_vehicles}")
    print(f"🚑 AMBULANCES: {detected_ambulances}")
    print(f"💥 DAMAGE: {detected_damage} (Highest: {highest_severity})")
    print(f"{'='*60}")

    # ===== VEHICLE COUNT =====
    ai_count = len(detected_vehicles)
    
    # ===== AMBULANCE LOGIC =====
    is_ambulance = len(detected_ambulances) > 0

    # ===== SIGNAL DECISIONS =====
    if is_ambulance:
        emergency_lane = 'north'
        signals = signal_controller.algorithm_emergency_corridor(emergency_lane)
        sig_status = {lane: 'red' for lane in signal_controller.lanes.keys()}
        sig_status[signals.green_lane] = 'green'
    else:
        sig_status = decide_signals_smart(ai_count)

    if signal_controller:
        for lane_name in signal_controller.lanes.keys():
            if lane_name not in sig_status:
                sig_status[lane_name] = 'red'

    # ===== STATUS DETERMINATION =====
    raw_stat = "Normal"
    
    if highest_severity == "Severe":
        raw_stat = "Accident"
    elif highest_severity == "Moderate":
        raw_stat = "Accident"
    elif highest_severity == "Minor":
        raw_stat = "Minor"
    elif ai_count > 12:
        raw_stat = "Traffic"

    stable_stat = status_stabilizer.add(raw_stat)
    current_time = time.time()

    # ===== INCIDENT HANDLING =====
    if signal_controller:
        if stable_stat == "Accident" and highest_severity == "Severe":
            signal_controller.mark_incident('north', IncidentLevel.SEVERE_ACCIDENT)
        elif stable_stat == "Accident":
            signal_controller.mark_incident('north', IncidentLevel.MINOR_ACCIDENT)
        else:
            signal_controller.clear_incident('north')

    if stable_stat in ["Accident"] and highest_severity != "None":
        last_time = last_alert_timers.get("Accident", 0)
        if current_time - last_time > ALERT_INTERVAL:
            print(f"🔥 INCIDENT: {highest_severity} Damage Detected")
            last_alert_timers["Accident"] = current_time
            incident_lock = True

            frame_to_save = frame.copy()
            t = threading.Thread(
                target=handle_alert_background,
                args=(
                    3 if highest_severity == "Severe" else 2,
                    f"{highest_severity.upper()} ACCIDENT DETECTED",
                    f"AI detected {highest_severity.lower()} damage at scene.",
                    frame_to_save,
                    highest_severity.lower(),
                ),
            )
            t.start()
            snapshot_frame = encode_frame(frame_to_save)

    elif stable_stat == "Normal" and incident_lock:
        if current_time - max(last_alert_timers.values(), default=0) > 10:
            incident_lock = False

    # ===== GPS DRIFT =====
    drift_lat = CAMERA_LAT + random.uniform(-0.00002, 0.00002)
    drift_lon = CAMERA_LON + random.uniform(-0.00002, 0.00002)

    # ===== TIMING CALCULATION =====
    timing_decision = signal_controller.decide_signals() if signal_controller else None
    green_lane = None
    time_remaining = 0

    if timing_decision:
        for lane, state in sig_status.items():
            if state == 'green':
                green_lane = lane
                elapsed = time.time() - signal_controller.last_switch_time
                cycle_duration = signal_controller.EMERGENCY_CYCLE_TIME if incident_lock else signal_controller.BASE_CYCLE_TIME
                time_remaining = max(0, int(cycle_duration - elapsed))
                break

    algorithm_info = {
        'active': 'Emergency Mode' if incident_lock else f'{current_algorithm.title()} Algorithm',
        'junction_type': f'{signal_controller.junction_type.value}-Way Intersection',
        'incident_status': f"{stable_stat} ({highest_severity})" if highest_severity != "None" else stable_stat,
        'algorithm': current_algorithm,
        'current_green_lane': green_lane,
        'time_remaining': time_remaining,
        'reason': timing_decision.reason if hasattr(timing_decision, 'reason') else 'Normal cycle'
    }

    payload = {
        "level": 0,
        "title": "SYSTEM NORMAL",
        "message": f"Traffic Normal. Vehicles: {ai_count}",
        "color": "#4caf50",
        "corridor": False,
        "confidence": f"{int(max_conf*100)}%",
        "snapshot": snapshot_frame,
        "car_count": ai_count,
        "signals": sig_status,
        "manual": manual_lane_data.copy(),
        "gps": [drift_lat, drift_lon],
        "incident_active": incident_lock,
        "algorithm": algorithm_info
    }

    if incident_lock:
        severity_colors = {"Severe": "red", "Moderate": "orange", "Minor": "yellow"}
        payload.update({
            "level": 3 if highest_severity == "Severe" else 2,
            "title": f"{highest_severity.upper()} ACCIDENT DETECTED",
            "color": severity_colors.get(highest_severity, "red"),
            "corridor": True
        })
    elif is_ambulance:
        payload.update({
            "title": "AMBULANCE DETECTED",
            "color": "#0000FF",
            "level": 3,
            "corridor": True,
        })
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
    junction_type: int


@app.post("/update-lanes")
async def update_lanes(d: LaneData):
    global manual_lane_data
    manual_lane_data = d.model_dump()
    return {"status": "ok"}


@app.post("/set-junction")
async def set_junction(config: JunctionConfig):
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
    
    print("🔄 SYSTEM RESET")
    return {"status": "reset"}


# ===== LOAD THREE SPECIALIZED MODELS =====
print("\n" + "="*70)
print("🔧 INITIALIZING TRIPLE MODEL SYSTEM - HIGH ACCURACY MODE")
print("="*70)

# Model 1: Vehicle Detection (Custom Trained)
try:
    vehicle_model = YOLO("vehicle_detecting.pt")
    print("✅ [MODEL 1] Vehicle Detection: vehicle_detecting.pt")
    print(f"   Classes: {list(vehicle_model.names.values())}")
except Exception as e:
    print(f"⚠️ Could not load vehicle_detecting.pt, using yolov8n.pt. Error: {e}")
    vehicle_model = YOLO("yolov8n.pt")

# Model 2: Ambulance Detection (Custom Trained)
try:
    ambulance_model = YOLO("ambulance_detection.pt")
    print("✅ [MODEL 2] Ambulance Detection: ambulance_detection.pt")
    print(f"   Classes: {list(ambulance_model.names.values())}")
except Exception as e:
    print(f"⚠️ Could not load ambulance_detection.pt, using vehicle model. Error: {e}")
    ambulance_model = vehicle_model

# Model 3: Damage Severity Classification (Custom Trained)
try:
    damage_model = YOLO("damage.pt")
    print("✅ [MODEL 3] Damage Severity: damage.pt")
    print(f"   Classes: {list(damage_model.names.values())}")
except Exception as e:
    print(f"⚠️ Could not load damage.pt, using vehicle model. Error: {e}")
    damage_model = vehicle_model

print("="*70)
print("🚀 ALL MODELS LOADED - SYSTEM READY")
print("="*70 + "\n")


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
            
            # ===== RUN ALL THREE MODELS IN PARALLEL =====
            vehicle_task = asyncio.to_thread(
                vehicle_model.track, frame, conf=0.20, persist=True, verbose=False
            )
            ambulance_task = asyncio.to_thread(
                ambulance_model.track, frame, conf=0.30, persist=True, verbose=False
            )
            damage_task = asyncio.to_thread(
                damage_model.track, frame, conf=0.35, persist=True, verbose=False
            )
            
            vehicle_results, ambulance_results, damage_results = await asyncio.gather(
                vehicle_task, ambulance_task, damage_task
            )
            
            data = await analyze_detections(
                vehicle_results, ambulance_results, damage_results,
                vehicle_model.names, ambulance_model.names, damage_model.names,
                frame
            )
            
            await websocket.send_json(data)
            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        print("Dashboard Disconnected")
    finally:
        vs.stop()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)