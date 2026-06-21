# SIH STARTUP QUICK START

## 3 WAYS TO START YOUR SYSTEM

### WAY 1: Windows Batch File (EASIEST - 1 CLICK)
```
C:\SIH\
    └─ START_SYSTEM.bat  ← DOUBLE-CLICK THIS

Result: Both backend and frontend start automatically
Time: ~30 seconds to full operation
Best for: Everyone
```

### WAY 2: Python Script (RECOMMENDED - 1 COMMAND)
```powershell
cd c:\SIH
python start_system.py

Result: Automatic startup + clean shutdown
Time: ~30 seconds to full operation
Best for: Command line users
```

### WAY 3: Manual 2-Terminal (FOR DEBUGGING)
```powershell
# Terminal 1
cd c:\SIH
python main.py

# Terminal 2
cd c:\SIH\dashboard
npm start

# Browser
http://localhost:3000
```

---

## WHAT STARTS

```
┌─────────────────────────────────────────┐
│   BACKEND                               │
│   Port: 8000                            │
│   Tech: Python FastAPI                  │
│   Models: 3 YOLO (Vehicle, Ambulance,   │
│             Damage)                     │
│   Status: ✓ Running                     │
└─────────────────────────────────────────┘
              ↕  WebSocket
┌─────────────────────────────────────────┐
│   FRONTEND                              │
│   Port: 3000                            │
│   Tech: React Dashboard                 │
│   Features: Signals, Algorithms,        │
│             Routing, Live Data          │
│   Status: ✓ Running                     │
└─────────────────────────────────────────┘
              ↓
        http://localhost:3000
```

---

## MANUAL START INSTRUCTIONS

**If you want to start things manually (not recommended):**

### Step 1: Start Backend (Port 8000)
```powershell
cd c:\SIH
python main.py
```

Wait for this message:
```
Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Start Frontend (Port 3000)
```powershell
cd c:\SIH\dashboard
npm start
```

Wait for this message:
```
Compiled successfully!
Local: http://localhost:3000
```

### Step 3: Open Browser
```
http://localhost:3000
```

### Step 4: Stop Everything
```
Backend Terminal: Ctrl+C
Frontend Terminal: Ctrl+C
Browser: Close tab
```

---

## HOW TO STOP

### If using START_SYSTEM.bat:
- Close the Backend window
- Close the Frontend window

### If using start_system.py:
- Press Enter in the PowerShell window
- All services shut down automatically

### If using Manual method:
- Press Ctrl+C in Backend terminal
- Press Ctrl+C in Frontend terminal

---

## EXPECTED OUTPUT

### Backend Console (You'll see)
```
INITIALIZING TRIPLE MODEL SYSTEM - HIGH ACCURACY MODE
OK [MODEL 1] Vehicle Detection: accident_v2.pt
OK [MODEL 2] Ambulance Detection: ambulance.pt
OK [MODEL 3] Damage Severity: damage.pt
ALL MODELS LOADED - SYSTEM READY
INFO: Uvicorn running on http://0.0.0.0:8000
INFO: Application startup complete
```

### Frontend Console (You'll see)
```
Compiled successfully!

You can now view traffic-command-dashboard in the browser.
Local: http://localhost:3000
```

### Browser (You'll see)
```
Status: Connected ✓
Algorithm: Adaptive
Junction: 4-Way
Signals Ready
Dashboard loaded
```

---

## WHAT YOU NEED

✓ Python installed (comes with your system)
✓ Node.js/npm installed (for React)
✓ Models at: c:\SIH\backend\models\*.pt
✓ Files at: c:\SIH\ and c:\SIH\dashboard\

Everything is already set up!

---

## MOST COMMON ISSUE & FIX

### "Port 8000/3000 already in use"

```powershell
# Kill old processes
taskkill /F /IM python.exe
taskkill /F /IM node.exe

# Try again
python start_system.py
```

---

## FULL DOCUMENTATION

Read these files in c:\SIH\ for more details:
- **HOW_TO_START.md** - Detailed startup guide
- **STARTUP_MANUAL.md** - Complete manual with troubleshooting
- **START_HERE.md** - Quick 5-minute overview
- **QUICK_REFERENCE.md** - Common commands

---

## TRY IT NOW

### Option 1 (Easiest):
```
1. Open C:\SIH in Windows Explorer
2. Double-click START_SYSTEM.bat
3. Wait 30 seconds
4. Dashboard opens automatically
5. Done!
```

### Option 2 (Command):
```powershell
cd c:\SIH
python start_system.py
# Dashboard opens automatically
# Press Enter to stop
```

---

**You're ready! Pick any method and launch your Smart Intelligent Highways system!**
