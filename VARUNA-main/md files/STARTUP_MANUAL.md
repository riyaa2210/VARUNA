# SMART INTELLIGENT HIGHWAYS - COMPLETE STARTUP MANUAL

## Option 1: ONE-CLICK STARTUP (RECOMMENDED)

### What It Does
Starts both backend and frontend automatically, checks if everything is working, opens dashboard in browser, and handles shutdown cleanly.

### How to Use

**Step 1:** Open PowerShell in the `c:\SIH` folder
- Right-click in Explorer → Open PowerShell here
- OR: Press `Win + X` → PowerShell → `cd c:\SIH`

**Step 2:** Run the startup script
```powershell
python start_system.py
```

**What Happens:**
1. ✓ Backend starts (port 8000) - AI models load, WebSocket ready
2. ✓ Health check - waits for backend to respond (max 20 sec)
3. ✓ Frontend starts (port 3000) - React compiles and launches
4. ✓ Browser opens - Dashboard appears at http://localhost:3000
5. ⏸ Script waits - Press Enter to shut everything down

**To Stop:**
- Press Enter in the PowerShell window where you ran `python start_system.py`
- All services will close cleanly

---

## Option 2: MANUAL STARTUP (TWO TERMINALS)

### For Advanced Users / Testing

**Terminal 1 - Backend:**
```powershell
cd c:\SIH
python main.py
```
Wait for output:
```
Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Frontend:**
```powershell
cd c:\SIH\dashboard
npm start
```
Wait for output:
```
Compiled successfully!
You can now view traffic-command-dashboard in the browser.
Local: http://localhost:3000
```

**Step 3 - Open Dashboard:**
Open browser → http://localhost:3000

**To Stop:**
- Terminal 1: Press `Ctrl+C`
- Terminal 2: Press `Ctrl+C`

---

## Option 3: BATCH FILE STARTUP (WINDOWS)

If you want a batch file that does the same as `start_system.py`:

**File: `c:\SIH\START.bat`**
```batch
@echo off
echo.
echo =============================================================
echo   SMART INTELLIGENT HIGHWAYS - LAUNCH SEQUENCE
echo =============================================================
echo.

cd /d c:\SIH

REM Start Backend in new window
echo [1/2] Starting AI Core on port 8000...
start "SIH-Backend" cmd /k python main.py

timeout /t 3

REM Start Frontend in new window
echo [2/2] Starting Dashboard on port 3000...
start "SIH-Frontend" cmd /k "cd dashboard && npm start"

timeout /t 5

REM Open browser
echo [3/3] Opening dashboard...
start http://localhost:3000

echo.
echo All systems online!
echo Close these windows to shutdown.
echo.
pause
```

**How to use:**
1. Save this as `c:\SIH\START.bat`
2. Double-click it
3. Both terminals open automatically
4. Dashboard appears in browser

---

## SYSTEM ARCHITECTURE (What's Running)

```
┌─────────────────────────────────────────────────────────┐
│           YOUR COMPLETE SIH SYSTEM                       │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  BACKEND (Port 8000)                                    │
│  ├─ Python FastAPI Server (main.py)                    │
│  ├─ 3 YOLO Models Running in Parallel                  │
│  │  ├─ accident_v2.pt (Vehicle Detection)              │
│  │  ├─ ambulance.pt (Ambulance Detection)              │
│  │  └─ damage.pt (Damage Classification)               │
│  ├─ Signal Algorithms (5 types)                        │
│  └─ WebSocket Streaming (ws://localhost:8000/ws)      │
│                                                           │
│  FRONTEND (Port 3000)                                   │
│  ├─ React Dashboard (traffic-command-dashboard)        │
│  ├─ Algorithm Selector                                 │
│  ├─ Junction Type Controller (2-6 way)                │
│  ├─ Real-time Signal Display                          │
│  ├─ Live Video Feed Integration                        │
│  ├─ Hospital Routing with ETA                          │
│  └─ Emergency Playbooks                                │
│                                                           │
│  COMMUNICATION                                          │
│  └─ WebSocket Connection                              │
│     (Backend ←→ Frontend)                              │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## FOLDER STRUCTURE (For Reference)

```
c:\SIH\
├── main.py                          [Backend entry point]
├── signal_algorithms.py             [5 traffic algorithms]
├── start_system.py                  [ONE-CLICK STARTUP]
├── start_system.bat                 [Windows batch version]
│
├── backend/models/                  [AI Models folder]
│   ├── accident_v2.pt              [Vehicle detector]
│   ├── ambulance.pt                [Ambulance detector]
│   ├── damage.pt                   [Damage classifier]
│   └── yolov8n.pt                  [Fallback detector]
│
├── dashboard/                       [React Frontend]
│   ├── package.json                [Dependencies config]
│   ├── public/                     [Static files]
│   │   ├── index.html
│   │   ├── manifest.json
│   │   └── favicon.ico
│   ├── src/                        [React source]
│   │   ├── App.js                 [Main dashboard]
│   │   ├── App.css                [Styles]
│   │   ├── index.js               [Entry point]
│   │   └── index.css              [Global styles]
│   └── node_modules/              [npm packages]
│
├── data/evidence_archive/          [Auto-organized evidence]
│   ├── minor/
│   ├── moderate/
│   └── severe/
│
├── archives/backup-code/           [Old versions]
│   └── old-trials/
│       ├── Try_1/
│       ├── Try_2/
│       └── ...
│
└── Documentation/
    ├── START_HERE.md
    ├── QUICK_REFERENCE.md
    ├── PROJECT_STRUCTURE.md
    └── ...
```

---

## COMMON COMMANDS QUICK REFERENCE

### Starting System
```powershell
# ONE-CLICK (BEST)
cd c:\SIH
python start_system.py

# MANUAL - Terminal 1
cd c:\SIH
python main.py

# MANUAL - Terminal 2
cd c:\SIH\dashboard
npm start

# Windows Batch
c:\SIH\start_system.bat
```

### Stopping System
```powershell
# From start_system.py: Press Enter
# From manual terminals: Ctrl+C (in each window)
# From batch file: Close the windows
```

### Checking Ports
```powershell
# Check if ports are in use
netstat -ano | Select-String "3000|8000"

# Kill specific port (if stuck)
taskkill /F /PID <PID>
```

### View Logs
```powershell
# Backend is running in separate console
# Frontend is running in separate console
# Check their console output directly
```

### npm Issues
```powershell
# If npm start fails
cd c:\SIH\dashboard
npm install           # Reinstall dependencies
npm start            # Try again

# Clear cache
npm cache clean --force
npm install
```

---

## STARTUP PROCESS TIMELINE

### Using `python start_system.py`

```
[00:00] Script started
        ↓
[00:01] Backend process spawned
        ↓
[00:02-00:20] Health check loop (checking http://localhost:8000/docs)
        ↓
[00:20] Backend responds ✓
        ↓
[00:21] Frontend process spawned (npm start)
        ↓
[00:25] React compilation complete ✓
        ↓
[00:26] Browser window opens
        ↓
[00:27] READY - Waiting for user to press Enter
        ↓
[User presses Enter]
        ↓
[00:XX] Taskkill terminates both processes cleanly
        ↓
[00:XX+] All windows close, system shutdown complete
```

**Total time to full operation: ~25-30 seconds**

---

## TROUBLESHOOTING

### Problem: Port 8000 already in use
```powershell
# Find what's using it
netstat -ano | Select-String ":8000"

# Kill that process
taskkill /F /PID <PID>

# Then retry
python start_system.py
```

### Problem: Port 3000 already in use
```powershell
netstat -ano | Select-String ":3000"
taskkill /F /PID <PID>
```

### Problem: npm start fails
```powershell
cd c:\SIH\dashboard
npm install
npm start
```

### Problem: Backend won't start
```powershell
# Check if main.py exists
Test-Path c:\SIH\main.py

# Check if models exist
Test-Path c:\SIH\backend\models\*.pt

# Try running manually
cd c:\SIH
python main.py
```

### Problem: Browser won't open
- Manual browser: Open http://localhost:3000 in Chrome/Firefox/Edge
- Check if React compiled: Look at Frontend terminal for "Compiled successfully!"

---

## WHAT YOU GET

### Using start_system.py
✓ Both services start automatically
✓ Health checks before proceeding
✓ Browser opens automatically
✓ Clean shutdown on Enter key
✓ Error handling and fallbacks
✓ No manual terminal management needed

### Using Manual Startup
✓ More control over each service
✓ See real-time logs from both terminals
✓ Can restart individual services
✓ Better for debugging

---

## NEXT STEPS AFTER STARTUP

1. **Dashboard loads** → http://localhost:3000
2. **Select Algorithm** → Choose from Adaptive/Zone/Weighted
3. **Select Junction Type** → 2-way to 6-way
4. **View Live Data** → Real-time signals, traffic, video
5. **Test Features** → Click buttons, adjust sliders
6. **Simulate Event** → Click "SIMULATE CRASH" button

---

## SHUTDOWN PROCEDURE

### Clean Shutdown
```powershell
# If using start_system.py:
[Press Enter in the script window]

# If using manual terminals:
# Terminal 1: Ctrl+C
# Terminal 2: Ctrl+C
# Browser: Close the tab
```

### Force Shutdown (if stuck)
```powershell
taskkill /F /T /PID <PID>
# Or
taskkill /F /IM python.exe
taskkill /F /IM node.exe
```

---

## SUCCESS INDICATORS

✓ Backend: "Uvicorn running on http://0.0.0.0:8000"
✓ Frontend: "Compiled successfully!"
✓ Browser: Shows green "Connected" badge
✓ WebSocket: No errors in console
✓ Models: All 4 YOLO models loaded

---

**You're all set! Use `python start_system.py` for the easiest experience.**
