import os
import time
import numpy as np
import cv2

# Load env token like other scripts
token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')
# Try ../.env if not set
if not token or not chat_id:
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip().startswith('TELEGRAM_BOT_TOKEN') and not token:
                    token = line.split('=',1)[1].strip()
                if line.strip().startswith('TELEGRAM_CHAT_ID') and not chat_id:
                    chat_id = line.split('=',1)[1].strip()

if not token:
    raise SystemExit('TELEGRAM_BOT_TOKEN not found in env or ../.env')
if not chat_id:
    print('TELEGRAM_CHAT_ID not found; using previously known value if available')

# Create a dummy frame (or reuse test.jpg)
img_path = os.path.join(os.path.dirname(__file__), 'test.jpg')
if os.path.exists(img_path):
    frame = cv2.imread(img_path)
else:
    frame = np.zeros((480,640,3), dtype=np.uint8)
    cv2.putText(frame, 'SIMULATED INCIDENT', (30,240), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255), 2)
    cv2.imwrite(img_path, frame)

# Import main and call the background alert handler directly
print('[SIM] Importing main...')
import main

print('[SIM] Triggering ACCIDENT alert...')
main.handle_alert_background(2, 'ACCIDENT DETECTED', 'Simulated test: Accident', frame.copy(), 'Accident')
# Wait a short time between alerts
time.sleep(3)
print('[SIM] Triggering FIRE alert...')
main.handle_alert_background(3, 'FIRE DETECTED', 'Simulated test: Fire', frame.copy(), 'Fire')

print('[SIM] Done. Check your Telegram for photo(s) and location message(s).')
