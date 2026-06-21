# COMPLETE SYSTEM INTEGRATION GUIDE

## ✅ NO CODE CHANGES NEEDED

All your files are **100% compatible** with the new triple-model main.py:

### File Status:
```
✅ main.py              → NEW Enhanced Triple-Model (DEPLOYED)
✅ App.js               → Frontend Dashboard (NO CHANGES)
✅ App.css              → Styling & Animations (NO CHANGES)
✅ signal_algorithms.py → Smart Traffic Control (NO CHANGES)
✅ start_system.py      → System Launcher (NO CHANGES)
```

---

## DATA FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMERA FEED INPUT                        │
│              (Real Camera or Synthetic Mode)                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   TRIPLE MODEL SYSTEM        │
        │ (Running in Parallel)        │
        ├──────────────────────────────┤
        │ Model 1: vehicle_detecting   │ → Count cars/buses/trucks
        │ Model 2: ambulance_detection │ → Detect emergency vehicles
        │ Model 3: damage.pt           │ → Classify severity
        └──────────┬───────────────────┘
                   │
        ┌──────────▼──────────────┐
        │  SEVERITY ANALYSIS      │
        ├────────────────────────┤
        │ Severe   → RED     → Incident
        │ Moderate → ORANGE  → Incident
        │ Minor    → YELLOW  → Logged
        │ None     → GREEN   → Normal
        └──────────┬──────────────┘
                   │
        ┌──────────▼───────────────────────┐
        │   SMART SIGNAL CONTROLLER        │
        │ (signal_algorithms.py)           │
        ├──────────────────────────────────┤
        │ Algorithm Selection:             │
        │ [1] Normal Adaptive (traffic)    │
        │ [2] Accident Diversion           │
        │ [3] Emergency Corridor (ambulance)
        │ [4] Fire Evacuation              │
        │ [5] Multi-Accident               │
        └──────────┬──────────────────────┘
                   │
        ┌──────────▼──────────────────────┐
        │   SIGNAL DECISION                │
        ├──────────────────────────────────┤
        │ North:  RED    (10s wait)
        │ East:   GREEN  (5s active)
        │ South:  RED    (10s wait)
        │ West:   RED    (10s wait)
        └──────────┬──────────────────────┘
                   │
        ┌──────────▼──────────────────────┐
        │  WEBSOCKET BROADCAST             │
        │  (to React Dashboard)            │
        ├──────────────────────────────────┤
        │ {                                │
        │   "signals": {...},              │
        │   "algorithm": {                 │
        │     "active": "Adaptive",        │
        │     "current_green_lane": "east",│
        │     "time_remaining": 5,         │
        │     "reason": "5 vehicles"       │
        │   },                             │
        │   "car_count": 5,                │
        │   "gps": [15.45, 75.01],         │
        │   "level": 0                     │
        │ }                                │
        └──────────┬──────────────────────┘
                   │
        ┌──────────▼──────────────────────┐
        │  REACT DASHBOARD RENDERS         │
        │  (App.js + App.css)              │
        ├──────────────────────────────────┤
        │ [LIVE VIDEO] [SIGNAL GRID]       │
        │ [TIMER BOX]  [ALGORITHM INFO]    │
        │ [MAP]        [EMERGENCY PLAYBOOK]│
        │ [LOGS]       [CONTROLS]          │
        └──────────────────────────────────┘
```

---

## COMPONENT INTEGRATION MATRIX

### Frontend ↔ Backend Communication

| Feature | App.js | main.py | Endpoint | Status |
|---------|--------|---------|----------|--------|
| **Algorithm Selection** | Select dropdown | Sets `current_algorithm` | `/set-algorithm` | ✅ Works |
| **Junction Type** | Buttons 2-6 way | Creates `signal_controller` | `/set-junction` | ✅ Works |
| **Live Timer** | `algorithmInfo.time_remaining` | Calculates from cycle_time | WebSocket payload | ✅ Works |
| **Signal Grid** | Renders all lanes | Updates from algorithm | WebSocket `signals` | ✅ Works |
| **Emergency Playbook** | Shows Algorithm #2-4 | Marks incidents | WebSocket `level` | ✅ Works |
| **Lane Sliders** | East/South/West inputs | Updates `manual_lane_data` | `/update-lanes` | ✅ Works |
| **GPS Display** | Shows coordinates | Adds noise to location | WebSocket `gps` | ✅ Works |
| **Evidence Photo** | Displays in center | Captures on incident | WebSocket `snapshot` | ✅ Works |
| **Vehicle Count** | Traffic level bar | From Model 1 detection | WebSocket `car_count` | ✅ Works |
| **Ambulance Alert** | Audio + Visual | Model 2 detection | WebSocket `title` | ✅ Works |

---

## API ENDPOINTS REFERENCE

### All endpoints provided by new main.py:

#### 1. **POST /update-lanes**
```json
Request:  { "east": 10, "south": 5, "west": 8 }
Response: { "status": "ok" }
Called by: Lane slider changes in App.js
```

#### 2. **POST /set-junction**
```json
Request:  { "junction_type": 4 }
Response: { "status": "ok", "junction": "FOUR_WAY" }
Called by: Junction type selector in App.js
```

#### 3. **POST /set-algorithm**
```json
Request:  { "algorithm": "weighted" }
Response: { "status": "ok", "algorithm": "weighted" }
Called by: Algorithm dropdown in App.js
```

#### 4. **POST /reset-system**
```json
Request:  {}
Response: { "status": "reset" }
Called by: Reset button in App.js
```

#### 5. **WS /ws** (WebSocket)
```json
Broadcast every frame:
{
  "level": 0,                          // 0=Normal, 1=Traffic, 2=Accident, 3=Severe
  "title": "SYSTEM NORMAL",
  "message": "Traffic Normal. Vehicles: 5",
  "color": "#4caf50",
  "corridor": false,
  "confidence": "85%",
  "snapshot": null,
  "car_count": 5,
  "signals": {
    "north": "red",
    "east": "green",
    "south": "red",
    "west": "red"
  },
  "manual": {
    "east": 10,
    "south": 5,
    "west": 8
  },
  "gps": [15.459234, 75.008456],
  "incident_active": false,
  "algorithm": {
    "active": "Adaptive Algorithm",
    "junction_type": "4-Way Intersection",
    "incident_status": "Normal (None)",
    "algorithm": "adaptive",
    "current_green_lane": "east",
    "time_remaining": 5,
    "reason": "5 vehicles in east"
  }
}
```

---

## EXECUTION FLOW (DETAILED)

### Step 1: System Startup
```
User runs: python start_system.py
           ↓
Validates main.py exists ✅
Activates virtual env ✅
Starts: python main.py
           ↓
Loads 3 YOLO models (with fallbacks) ✅
Creates SmartSignalController ✅
Starts VideoStream (camera or synthetic) ✅
Starts FastAPI uvicorn server ✅
           ↓
start_system.py detects server ready ✅
Starts: npm start (React)
           ↓
React compiles + opens browser ✅
http://localhost:3000 loads
```

### Step 2: Frame Processing (Repeating)
```
Camera/Synthetic Input
           ↓
asyncio.gather() runs 3 models in parallel:
  - vehicle_model.track()
  - ambulance_model.track()
  - damage_model.track()
           ↓
analyze_detections() extracts:
  - detected_vehicles (count + names)
  - detected_ambulances (boolean flag)
  - detected_damage (severity classification)
           ↓
signal_controller.update_traffic_data()
signal_controller.mark_incident() [if needed]
signal_controller.decide_signals() [algorithm selection]
           ↓
Build payload with:
  - signals (green/red per lane)
  - algorithm_info (active mode, timer, reason)
  - car_count, gps, snapshot, level, etc.
           ↓
WebSocket broadcast to all connected clients
           ↓
App.js receives → setState() updates → React re-renders
           ↓
Dashboard shows:
  - Live timer countdown
  - Signal grid with green highlight
  - Emergency playbook (if incident)
  - Vehicle count bar
  - GPS coordinates
```

### Step 3: User Interaction
```
User clicks: "Weighted Algorithm"
           ↓
App.js calls: POST /set-algorithm with { algorithm: "weighted" }
           ↓
main.py updates: current_algorithm = "weighted"
signal_controller.algorithm_mode = "weighted"
           ↓
Next frame uses weighted priority algorithm
           ↓
WebSocket sends: algorithm.active = "Weighted Priority"
           ↓
Dashboard updates: Shows new algorithm name + reason
```

---

## SIGNAL TIMING EXAMPLES

### Scenario 1: Normal Adaptive Mode
```
Input Traffic:
  North: 15 vehicles (high)
  East:  3 vehicles (low)
  South: 8 vehicles (medium)
  West:  2 vehicles (low)

Algorithm: Normal Adaptive (weighted by traffic)
Decision: "Adaptive: 15 vehicles in north"

Output Signals:
  North: GREEN (15s) → Highest traffic
  East:  RED
  South: RED
  West:  RED

After 15s, next cycle starts with east
```

### Scenario 2: Accident Detection
```
Input: Damage.pt detects "SEVERE" in north lane
       vehicle_count: 10 vehicles

Algorithm: Accident Diversion (Algorithm #2)
Decision: "Diversion from blocked north"

Output Signals:
  North: RED (BLOCKED)
  East:  GREEN (30s) → Priority for diversion
  South: GREEN (opposite) → Allows escape
  West:  RED

System sends: level=3, title="SEVERE ACCIDENT"
Dashboard shows: Red overlay + emergency playbook
Telegram alert: Sends photo with incident details
```

### Scenario 3: Ambulance Detected
```
Input: ambulance_detection.pt finds ambulance heading north

Algorithm: Emergency Corridor (Algorithm #3)
Decision: "EMERGENCY CORRIDOR: NORTH"

Output Signals:
  North: GREEN (60s) ← LONG GREEN for ambulance
  East:  RED
  South: RED
  West:  RED

System sends: level=3, title="AMBULANCE DETECTED", corridor=true
Dashboard shows: Blue flashing border + audio alert
Timeline: GREEN for 60 seconds regardless of traffic
```

---

## ERROR HANDLING & FALLBACKS

### Model Loading
```
Try: vehicle_detecting.pt
  ↓ (if fails)
Use: yolov8n.pt (general object detection)
Result: Vehicle counting still works (slightly less accuracy)

Try: ambulance_detection.pt
  ↓ (if fails)
Use: vehicle_model (fallback to vehicle detection)
Result: Ambulances detected as "vehicle" (false positives possible)

Try: damage.pt
  ↓ (if fails)
Use: vehicle_model (fallback to vehicle detection)
Result: Damage not classified (no severity levels)
```

### Camera Failure
```
Try: cv2.VideoCapture(MOBILE_CAMERA_URL)
  ↓ (if frames.read() fails)
Synthetic Video Mode activates automatically:
  - Black frame with moving colored boxes
  - Shows "NO CAMERA - SIMULATION MODE" text
  - Continues processing as if real video
Result: System keeps running for testing
```

### Signal Algorithm Issue
```
Try: Import SmartSignalController
  ↓ (if ImportError)
signal_controller = None
  ↓
Use fallback in decide_signals_smart():
  return {"north": "green", "east": "red", ...}
Result: Basic fixed signal timing (no adaptive)
```

---

## PRODUCTION DEPLOYMENT CHECKLIST

- [x] All dependencies installed
- [x] Virtual environment activated
- [x] main.py compiles without errors
- [x] App.js expects correct WebSocket payload
- [x] signal_algorithms.py provides all methods
- [x] start_system.py points to correct paths
- [x] Evidence storage folders created
- [x] Telegram credentials configured
- [x] Camera URL set (or synthetic mode ready)
- [x] Port 8000 (backend) available
- [x] Port 3000 (frontend) available
- [x] CORS enabled for all origins
- [x] WebSocket reconnection logic active

---

## QUICK START (3 STEPS)

### Method 1: Automated Launch
```powershell
cd C:\SIH
python start_system.py
# Automatic startup + browser open
# Press Enter to shutdown
```

### Method 2: Manual Launch
```powershell
# Terminal 1:
cd C:\SIH
python main.py

# Terminal 2:
cd C:\SIH\dashboard
npm start

# Terminal 3:
# Open: http://localhost:3000
```

### Method 3: Development Mode
```powershell
# Run backend with output
cd C:\SIH
python main.py

# In another terminal, watch frontend
cd C:\SIH\dashboard
npm start

# Open DevTools (F12) in browser to see console logs
```

---

## SUPPORT INFORMATION

### To debug issues:
1. Check backend console for: `VEHICLES:`, `AMBULANCES:`, `DAMAGE:` logs
2. Check browser console (F12) for WebSocket messages
3. Check `/evidence_archive/` folders for saved images
4. Verify camera URL in main.py is correct
5. Verify Telegram credentials if alerts needed

### To test without camera:
- Synthetic video mode auto-activates when camera unavailable
- Use lane sliders to simulate traffic scenarios
- Use "SIMULATE CRASH" button to trigger accident detection
- Use "RESET SYSTEM" to clear incidents

### Common Issues & Solutions:
```
Issue: WebSocket connection failed
Fix:   Make sure main.py is running on localhost:8000

Issue: Models not loading
Fix:   Check if .pt files exist in C:\SIH directory
      System will use yolov8n.pt as fallback

Issue: Dashboard blank
Fix:   Check browser console for errors
      Verify WebSocket URL is correct

Issue: No video feed
Fix:   Update MOBILE_CAMERA_URL to your camera IP
      Or leave default for synthetic video mode
```

---

**✅ SYSTEM IS FULLY INTEGRATED AND PRODUCTION-READY**
