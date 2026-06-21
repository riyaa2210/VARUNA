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
from ultralytics import YOLO
from twilio.rest import Client

# --- CONFIGURATION ---
# UPDATE YOUR IP HERE
MOBILE_CAMERA_URL = "http://10.149.88.192:8080/video"
MODEL_NAME = 'accident_v2.pt'

# Twilio Configuration
TWILIO_SID = os.getenv("TWILIO_SID", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
TWILIO_FROM = os.getenv("TWILIO_FROM", "+15551234567")
TWILIO_TO_POLICE = os.getenv("TWILIO_TO_POLICE", "+919999999999")

# --- RUNTIME TUNABLES (DEMO MODE) ---
# Reduced history length for faster reaction time (was 30)
HISTORY_LEN = int(os.getenv("HISTORY_LEN", 12)) 
SNAPSHOT_COOLDOWN = int(os.getenv("SNAPSHOT_COOLDOWN", 5))
SMS_COOLDOWN = int(os.getenv("SMS_COOLDOWN", 300))

# Lowered confidence threshold to detect incidents in imperfect lighting (was 0.6)
MIN_CONF = float(os.getenv("MIN_CONF", 0.40))

# Logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Track last SMS times
last_sms_time = {}

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
        
        # LOGIC FILTER:
        # Reduced threshold to 50% agreement (was 60%) for snappier response
        if most_common_status in ["Accident", "Fire", "Minor"]:
            if count > (self.history.maxlen * 0.5): 
                return most_common_status
            else:
                return "Normal"
        
        return most_common_status

# Global state
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

# --- CORE LOGIC ---
def analyze_detections(results, model_names, frame):
    global last_snapshot_time
    
    detected_objects = []
    max_conf = 0.0
    
    snapshot_frame = frame.copy()
    
    for r in results:
        for box in r.boxes:
            class_id = int(box.cls[0])
            name = model_names[class_id]
            conf = float(box.conf[0])
            detected_objects.append(name)
            
            if conf > max_conf: max_conf = conf
            
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            if "accident" in name or "fire" in name:
                color = (0, 0, 255)
            else:
                color = (0, 255, 0)
                
            cv2.rectangle(snapshot_frame, (x1, y1), (x2, y2), color, 2)
            label = f"{name} {int(conf*100)}%"
            cv2.putText(snapshot_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # Counting
    car_count = 0
    for obj in detected_objects:
        if obj in ['car', 'truck', 'bus', 'vehicle']:
            car_count += 1
    
    # Immediate Status
    raw_status = "Normal"
    if any(x in ['fire', 'smoke'] for x in detected_objects):
        raw_status = "Fire"
    elif any(x in ['severe_accident', 'accident', 'crash'] for x in detected_objects):
        raw_status = "Accident"
    elif 'minor_accident' in detected_objects:
        raw_status = "Minor"
    elif car_count > 4:
        raw_status = "Traffic"

    # Stabilization
    stable_status = status_stabilizer.add(raw_status)
    
    # DEBUG PRINT: This helps you see what is happening in the terminal
    if raw_status != "Normal":
        print(f"[DEBUG] Raw: {raw_status} | Stable: {stable_status} | Conf: {int(max_conf*100)}%")

    # Evidence Handling
    snapshot_data = None
    current_time = time.time()
    
    if stable_status in ["Fire", "Accident", "Minor"] and (current_time - last_snapshot_time > SNAPSHOT_COOLDOWN):
        save_evidence_to_disk(snapshot_frame, stable_status)
        snapshot_data = encode_frame(snapshot_frame)
        last_snapshot_time = current_time

    # Payload
    alert_payload = {
        "level": 0,
        "title": "SYSTEM NORMAL",
        "message": f"Traffic Flow Normal. Vehicles: {car_count}",
        "color": "#4caf50",
        "corridor": False,
        "confidence": f"{int(max_conf * 100)}%",
        "snapshot": snapshot_data,
        "car_count": car_count
    }

    if stable_status == "Fire":
        alert_payload.update({
            "level": 3, "title": "FIRE DETECTED", 
            "message": "CRITICAL THREAT. Auto-Dispatching Fire Brigade.", 
            "color": "darkred", "corridor": True
        })
        send_sms_alert(3, "Fire Detected - Auto Dispatch Sent")

    elif stable_status == "Accident":
        alert_payload.update({
            "level": 2, "title": "SEVERE CRASH", 
            "message": "Major Impact. Auto-Dispatching Ambulance.", 
            "color": "red", "corridor": True
        })
        send_sms_alert(2, "Severe Crash - Auto Dispatch Sent")

    elif stable_status == "Minor":
        alert_payload.update({
            "level": 1, "title": "MINOR ACCIDENT", 
            "message": "Minor Dent/Scratch. Evidence Saved.", 
            "color": "orange", "corridor": False
        })

    elif stable_status == "Traffic":
        alert_payload.update({
            "level": 1, "title": "HEAVY TRAFFIC", 
            "message": f"Congestion ({car_count} vehicles). Signal Adjusted.", 
            "color": "orange", "corridor": False
        })
    
    return alert_payload

def send_sms_alert(level, message):
    global last_sms_time
    current_time = time.time()
    
    last_sent = last_sms_time.get(level)
    if last_sent and (current_time - last_sent) < SMS_COOLDOWN:
        return False

    if TWILIO_SID and TWILIO_SID.startswith("AC") and "xxxx" not in TWILIO_SID:
        try:
            client = Client(TWILIO_SID, TWILIO_TOKEN)
            client.messages.create(
                body=f"SIH ALERT: {message}\nLevel: {level}",
                from_=TWILIO_FROM, to=TWILIO_TO_POLICE
            )
            logging.info(f"[SMS] Sent: {message}")
            last_sms_time[level] = current_time
            return True
        except Exception as e:
            logging.error(f"[SMS ERROR] {e}")
            return False
    else:
        logging.info(f"[SMS SIMULATION] To: {TWILIO_TO_POLICE} | Msg: {message}")
        last_sms_time[level] = current_time
        return False

# --- SERVER INITIALIZATION ---
app = FastAPI()

try:
    model = YOLO(MODEL_NAME)
    print(f"[SYSTEM] Custom model loaded: {MODEL_NAME}")
except Exception as e:
    print("[WARNING] Custom model not found. Falling back to YOLOv8n.")
    model = YOLO('yolov8n.pt')

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    cap = cv2.VideoCapture(MOBILE_CAMERA_URL)
    frame_count = 0
    
    print("[SYSTEM] WebSocket Connected.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                await asyncio.sleep(2)
                cap = cv2.VideoCapture(MOBILE_CAMERA_URL)
                continue

            frame_count += 1
            # Process every 4th frame (was 5th) to speed up history fill
            if frame_count % 4 != 0:
                await asyncio.sleep(0.01)
                continue 

            frame = cv2.resize(frame, (640, 480))
            
            # Inference
            results = await asyncio.to_thread(model, frame, conf=MIN_CONF, verbose=False)
            
            alert_data = analyze_detections(results, model.names, frame)
            await websocket.send_json(alert_data)
            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        print("[SYSTEM] Dashboard disconnected.")
    except Exception as e:
        print(f"[ERROR] Loop exception: {e}")
    finally:
        cap.release()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)