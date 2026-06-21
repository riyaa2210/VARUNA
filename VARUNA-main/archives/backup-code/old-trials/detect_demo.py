import cv2
from ultralytics import YOLO

# 1. Load the AI Model
# We use 'yolov8n.pt' (Nano) for now because it is fast and free.
# Later, you will change this to 'best.pt' to detect Fire/Accidents.
print("Loading AI Model...")
model = YOLO('yolov8n.pt')
print("AI Model Loaded!")

# 2. Connect to the Mobile Camera
# REPLACE with your exact phone URL (don't forget /video)
url = "http://192.168.0.4:8080/video" 

cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("Error: Could not connect to camera.")
    exit()

print("Starting Detection... Press 'q' to quit.")

while True:
    # Read a frame from the camera
    ret, frame = cap.read()
    if not ret:
        print("Stream ended.")
        break

    # Optional: Resize for faster processing/better fit
    frame = cv2.resize(frame, (640, 480))

    # 3. THE MAGIC STEP: Run YOLOv8 on the frame
    # conf=0.5 means "Only show things you are 50% sure about"
    results = model(frame, conf=0.5, verbose=False)

    # 4. Visualize the results
    # This draws the boxes and labels (like 'car', 'person') on the frame
    annotated_frame = results[0].plot()

    # Show the video on screen
    cv2.imshow("SIH 2025 - Proactive Detection", annotated_frame)

    # Press 'q' to quit
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()