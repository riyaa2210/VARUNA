# 🎥 IP Webcam App Setup Guide - VARUNA Traffic Management System

## Overview
This application uses an IP camera (typically from an Android mobile device) as the video source for real-time accident detection and traffic management. The system will automatically process video frames and detect incidents.

---

## Prerequisites
✅ **All dependencies are now installed:**
- Python 3.13 with required packages (OpenCV, FastAPI, YOLO, etc.)
- Node.js and npm with React dashboard dependencies
- YOLO accident detection models pre-trained

---

## Step 1: Set Up IP Webcam App on Mobile Phone

### For Android Devices:
1. **Download & Install "IP Webcam Pro" or "OWLRP" app** from Google Play Store
   - Free alternatives: "IP Webcam" by Pavel Khlebovich
   - Premium: "IP Webcam Pro"

2. **Configure the App:**
   - Open the app on your Android phone
   - Go to **Settings:**
     - Video resolution: 1280x720 (or higher for better detection)
     - Video orientation: Auto or Landscape
     - Port: `8080` (default)
     - Enable authentication if desired
   - Click **"Start Server"** button

3. **Find Your Phone's IP Address:**
   - Your phone's local IP will be displayed on the app screen (e.g., `192.168.1.100`)
   - Alternative: Settings → Wi-Fi → Connected Network → IP Address

4. **Verify Connection in Browser:**
   - Open: `http://[YOUR_PHONE_IP]:8080/video`
   - Example: `http://192.168.1.100:8080/video`
   - You should see MJPEG video stream

---

## Step 2: Configure the System for Your IP Camera

### Option A: Using Environment Variable (Recommended)
```powershell
# Set environment variable before starting
$env:MOBILE_CAMERA_URL = "http://192.168.1.100:8080"

# Then run the system
python start_system.py
```

### Option B: Edit Configuration File
Edit `main.py` line ~65:
```python
# Change this line:
MOBILE_CAMERA_URL = os.getenv("MOBILE_CAMERA_URL", "http://10.24.5.246:8080/video")

# To your phone's IP:
MOBILE_CAMERA_URL = "http://192.168.1.100:8080"  # Replace with your IP
```

### Option C: Fallback Modes
If IP camera is unavailable, the system supports:
- **Local Webcam:** `MOBILE_CAMERA_URL = 0` (uses your laptop's camera)
- **Video File:** `MOBILE_CAMERA_URL = "video.mp4"`

---

## Step 3: Run the System

### Start Everything (Backend + Frontend):
```powershell
cd C:\Users\sharm\Downloads\VARUNA\PROJECT\NEW
python start_system.py
```

This will automatically:
1. ✅ Start **AI Backend** on `http://localhost:8000`
   - Video processing
   - Accident detection (YOLO)
   - Traffic signal control algorithms
   - WebSocket real-time feed to dashboard

2. ✅ Start **React Dashboard** on `http://localhost:3000`
   - Real-time video feed display
   - Incident alerts
   - Traffic metrics
   - Signal control panel

3. ✅ Open browser to `http://localhost:3000`

---

## Troubleshooting

### Issue: "Cannot connect to IP camera"
**Solution:**
1. Verify phone is connected to **same Wi-Fi network** as laptop
2. Check IP Webcam app is showing **"Server Running"**
3. Manually test: Open `http://192.168.1.100:8080/video` in browser
4. If that works, update your IP address in configuration
5. **Check for firewall:** Allow port 8080 in Windows Firewall

### Issue: Backend starts but camera is unavailable
**Solution:**
- The system will **automatically fallback to local webcam** if IP camera fails
- Check the terminal for messages like:
  ```
  [CAMERA] ✓ IP camera connected successfully!
  ```
  or
  ```
  [CAMERA] Falling back to local webcam...
  ```

### Issue: Dashboard not loading on localhost:3000
**Solution:**
1. Wait 5-10 seconds (React compilation takes time)
2. Manually refresh: `http://localhost:3000`
3. Check terminal for React errors
4. Verify Node.js is properly installed: `node --version`

### Issue: Video stream not appearing in dashboard
**Solution:**
1. Check backend is healthy: Visit `http://localhost:8000/docs`
2. Check WebSocket connection in browser console (F12)
3. Verify video source in backend logs

---

## Access the System

| Component | URL | Purpose |
|-----------|-----|---------|
| Dashboard | http://localhost:3000 | Main UI for monitoring |
| Backend API | http://localhost:8000 | REST API endpoints |
| Backend Docs | http://localhost:8000/docs | API documentation |
| Video Stream | http://192.168.1.100:8080/video | Direct camera feed |

---

## Accessing from Mobile (Local Network)

### Access Dashboard from Phone on Same Network:
1. Find your **laptop's IP address:**
   ```powershell
   ipconfig  # Look for IPv4 Address (e.g., 192.168.1.50)
   ```

2. Open browser on phone:
   ```
   http://[YOUR_LAPTOP_IP]:3000
   ```

3. Example:
   ```
   http://192.168.1.50:3000
   ```

---

## System Architecture

```
Mobile Phone (IP Webcam App)
      ↓ (MJPEG Stream)
      ↓
Backend Server (main.py)
  ├─ YOLO v8 Accident Detection
  ├─ Traffic Signal Algorithms
  ├─ Incident Processing
  └─ WebSocket → Frontend
      ↓
React Dashboard (localhost:3000)
  ├─ Real-time Video Display
  ├─ Incident Alerts
  ├─ Traffic Metrics
  └─ Signal Control
```

---

## Performance Notes

- **Frame Processing:** 30 FPS (depends on model and phone resolution)
- **Detection Latency:** ~100-200ms per frame
- **Network:** Requires stable Wi-Fi connection between phone and laptop
- **Recommended Phone Resolution:** 1280x720 or higher
- **Model:** YOLO v8 Nano (optimized for real-time detection)

---

## Advanced Configuration

### Change Detection Confidence Threshold:
Edit `main.py` line ~101:
```python
MIN_CONF = 0.25  # Lower = more detections, higher = fewer false positives
```

### Change Junction Type:
Edit `main.py` line ~108:
```python
JunctionType.FOUR_WAY  # Can be: TWO_WAY, THREE_WAY, FOUR_WAY, FIVE_WAY, SIX_WAY
```

### Enable Telegram Alerts:
```powershell
$env:TELEGRAM_BOT_TOKEN = "your_bot_token"
$env:TELEGRAM_CHAT_ID = "your_chat_id"
```

---

## Stopping the System

Press **Enter** in the main terminal window that shows:
```
SYSTEM IS LIVE. Press Enter here to shut down all services.
```

This will gracefully close:
- React development server
- Python backend server
- All processes

---

## Support

For issues, check:
1. Console output for error messages
2. `http://localhost:8000/docs` - API documentation
3. Verify network connectivity between devices
4. Check firewall settings on both devices

