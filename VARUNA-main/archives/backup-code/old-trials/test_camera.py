import cv2

# REPLACE THIS with the URL from your phone screen
# IMPORTANT: You must add "/video" at the end to get the stream!
# Example: "http://192.168.1.5:8080/video"
url = "http://192.168.0.4:8080/video" 

print(f"Connecting to {url} ...")

# Connect to the stream
cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("Error: Could not connect to camera. Check Wi-Fi or URL.")
    exit()

print("Camera connected! Press 'q' to quit.")

while True:
    # 1. Get the frame (The "Eye" sends to "Brain")
    ret, frame = cap.read()
    
    if not ret:
        print("Stream ended or failed.")
        break

    # 2. Resize it slightly to fit your screen better (Optional)
    frame = cv2.resize(frame, (640, 480))

    # 3. Show it on the laptop screen
    cv2.imshow("My Mobile Eye", frame)

    # Press 'q' to exit
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()