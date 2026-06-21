# START HERE - Smart Intelligent Highways System

Your project is now professionally organized! Follow these steps to run the system.

## 📁 Project Organization

```
Backend    → /backend/        (Python + FastAPI)
Frontend   → /frontend/       (React Dashboard)
Models     → /backend/models/ (AI YOLO Weights)
Data       → /data/           (Evidence & Archives)
Backups    → /archives/       (Old Code & Trials)
Docs       → / (Root)         (All .md files)
```

## 🚀 Quick Start (3 Steps)

### Step 1: Start Backend (Terminal 1)
```bash
cd c:\SIH
python main.py
```

**Expected Output:**
```
INITIALIZING TRIPLE MODEL SYSTEM - HIGH ACCURACY MODE
OK [MODEL 1] Vehicle Detection: accident_v2.pt
OK [MODEL 2] Ambulance Detection: ambulance.pt
OK [MODEL 3] Damage Severity: damage.pt (Classification)
ALL MODELS LOADED - SYSTEM READY
Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Start Frontend (Terminal 2)
```bash
cd c:\SIH\frontend\dashboard
npm start
```

**Expected Output:**
```
Compiled successfully!
You can now view dashboard in the browser.
Local: http://localhost:3000
```

### Step 3: Open Dashboard
- Open browser → `http://localhost:3000`
- Select algorithm and junction type
- Watch real-time detection and signal control

## 📊 What Each Folder Does

### `/backend/` - AI & Signal Control
- **main.py**: FastAPI server running 3 YOLO models in parallel
- **signal_algorithms.py**: Smart signal control with 5 algorithms
- **start_system.py**: Batch file launcher
- **models/**: accident_v2.pt, ambulance.pt, damage.pt, yolov8n.pt

### `/frontend/dashboard/` - Judge Interface
- **App.js**: React component with WebSocket connection
- **index.html**: Dashboard entry point
- Features: timer, playbook, signal grid, algorithm selector

### `/data/evidence_archive/` - Incident Proof
- **minor/**: Minor accident evidence
- **moderate/**: Moderate accident evidence
- **severe/**: Severe accident evidence (auto-organized)

### `/archives/backup-code/` - Old Versions
- Previous main.py versions
- Experimental Try_1 through Try_5 folders
- Keep for reference, do NOT use

## 🎮 Using the Dashboard

1. **Algorithm Selector**: Choose between Adaptive, Zone, or Weighted
2. **Junction Type**: Select 2-way to 6-way intersection
3. **Timer**: Shows green signal countdown (real-time)
4. **Playbook**: Displays incident response status
5. **Signal Grid**: See current state of each lane (red/green)

## 🔍 Understanding the System

### Triple Model Architecture
1. **Vehicle Detection** (accident_v2.pt)
   - Detects: Fire, Smoke, Minor Accident, Severe Accident
   - Method: `.track()` with persistent ID tracking
   
2. **Ambulance Detection** (ambulance.pt)
   - Detects: Ambulance vehicles
   - Method: `.track()` with priority handling
   
3. **Damage Classification** (damage.pt)
   - Classifies: Minor, Moderate, Severe damage
   - Method: `.predict()` (classification, not detection)

### Signal Control Algorithms
- **Adaptive**: Dynamic real-time traffic flow
- **Zone**: Predefined time-based cycles
- **Weighted**: Priority-based allocation
- **Emergency**: Automatic corridor clearance
- **Multi-Accident**: Multi-zone incident management

## ⚙️ Configuration

### Backend Settings (main.py)
```python
MOBILE_CAMERA_URL = "http://10.125.48.115:8080/video"  # Camera source
TELEGRAM_BOT_TOKEN = "..."                               # Alert token
TELEGRAM_CHAT_ID = "..."                                 # Alert recipient
```

### API Endpoints
```
POST /update-lanes    - Send manual lane data
POST /set-junction    - Change junction type (2-6)
POST /set-algorithm   - Select algorithm (adaptive/zone/weighted)
```

## 🐛 Troubleshooting

### Backend won't start
- Check Python version: `python --version` (3.9+)
- Install dependencies: `pip install -r requirements.txt`
- Check if port 8000 is available

### Frontend won't start
- Navigate to correct folder: `cd c:\SIH\frontend\dashboard`
- Install dependencies: `npm install`
- Check if port 3000 is available

### Models won't load
- Verify files exist in `/backend/models/`
- Check file paths in main.py start with `backend/models/`
- Try fallback: yolov8n.pt should always work

### No camera feed
- System uses synthetic fallback (black frame with moving boxes)
- Update MOBILE_CAMERA_URL if using mobile camera
- WebSocket connection shown in browser console

## 📝 Important Files to Know

| File | Purpose |
|------|---------|
| `main.py` | Backend FastAPI + YOLO inference |
| `signal_algorithms.py` | Signal control logic |
| `PROJECT_STRUCTURE.md` | This folder organization |
| `README_FINAL_ANSWER.md` | Complete technical documentation |
| `QUICK_START.md` | Setup instructions |
| `frontend/dashboard/src/App.js` | React dashboard |

## 🔗 Port Mapping

- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **WebSocket**: ws://localhost:8000/ws

## 📱 Mobile Camera Setup

To use mobile camera instead of synthetic:
1. Install IP Webcam on Android phone
2. Note the IP:PORT from app
3. Update `MOBILE_CAMERA_URL` in main.py
4. Restart backend

## 🎯 Next Steps

1. ✅ Start backend (`python main.py`)
2. ✅ Start frontend (`npm start`)
3. ✅ Open dashboard (http://localhost:3000)
4. ✅ Test algorithms and junction types
5. ✅ Watch real-time detections in evidence archive

## 📞 System Status

- ✅ Backend: Running triple-model AI system
- ✅ Frontend: React dashboard with WebSocket
- ✅ Models: All 3 models loading successfully
- ✅ Signals: Multi-route algorithms ready
- ✅ Evidence: Auto-organized by severity
- ✅ Backups: Safe archived in `/archives/`

---

**Ready?** Run `python main.py` and `npm start` now!
