# HOW TO START YOUR SIH SYSTEM - COMPLETE GUIDE

## EASIEST WAY: Windows Batch File (ONE CLICK)

### For Non-Technical Users

**Step 1:** Go to `c:\SIH` folder in Windows Explorer

**Step 2:** Find `START_SYSTEM.bat` and double-click it

**That's it!** The system will:
- Open a Backend terminal (port 8000)
- Open a Frontend terminal (port 3000)
- Automatically open your Dashboard in the browser

**Visual:**
```
┌─────────────────────────────────────┐
│  Windows Explorer                   │
├─────────────────────────────────────┤
│ C:\SIH\                             │
│ ├─ START_SYSTEM.bat  ← DOUBLE CLICK│
│ ├─ main.py                          │
│ ├─ dashboard/                       │
│ └─ ...                              │
└─────────────────────────────────────┘
        ↓
  ✓ Backend starts
  ✓ Frontend starts
  ✓ Browser opens
  ✓ Dashboard ready at http://localhost:3000
```

---

## SECOND OPTION: Python Script (RECOMMENDED)

### For Users Who Like Commands

**Step 1:** Open PowerShell at `c:\SIH`
```
Windows Key → Type "PowerShell"
→ Right-click → "Run as Administrator"
→ Type: cd c:\SIH
```

**Step 2:** Run the Python startup script
```powershell
python start_system.py
```

**What Happens:**
```
[1/3] Initializing AI Core...
      (Virtual Env not found. Falling back to System Python)
      Backend starting on port 8000...

[2/3] Waiting for AI Core to respond...
      (Attempt 1/20...)
      (Attempt 2/20...)
      (AI Core is online!)

[3/3] Launching Command Dashboard...
      Opening browser...

============================================================
    SYSTEM IS LIVE. Press Enter here to shut down all services.
============================================================
```

**To Stop:** Press Enter in the PowerShell window

---

## THIRD OPTION: Manual Startup (FOR DEVELOPERS)

### If You Want Full Control

**Terminal 1 - Backend:**
```powershell
cd c:\SIH
python main.py
```

Wait for this message:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Terminal 2 - Frontend:**
```powershell
cd c:\SIH\dashboard
npm start
```

Wait for this message:
```
webpack compiled successfully
You can now view traffic-command-dashboard in the browser.
Local: http://localhost:3000
```

**Terminal 3 - Browser:**
```
Open: http://localhost:3000
```

**To Stop:**
- Terminal 1: Press `Ctrl+C`
- Terminal 2: Press `Ctrl+C`
- Close browser tab

---

## WHAT EACH OPTION DOES

| Method | Ease | Control | Best For |
|--------|------|---------|----------|
| **START_SYSTEM.bat** | ⭐⭐⭐⭐⭐ | Low | Users who want automatic |
| **python start_system.py** | ⭐⭐⭐⭐ | Medium | Most users |
| **Manual 3-Terminal** | ⭐⭐ | High | Developers/debugging |

---

## DETAILED STEP-BY-STEP: Using START_SYSTEM.bat

### Complete Walkthrough

**Step 1: Open Windows Explorer**
- Press `Windows Key + E`
- Navigate to `C:\SIH`

**Step 2: Locate the File**
```
C:\SIH\
├─ START_SYSTEM.bat  ← This one!
├─ main.py
├─ signal_algorithms.py
├─ start_system.py
└─ ... (other files)
```

**Step 3: Double-Click START_SYSTEM.bat**
- Right-click → "Run with PowerShell" (if Windows blocks it)
- Or just double-click normally

**Step 4: Watch the Startup**
```
Window 1: SIH-Backend
┌──────────────────────────────┐
│ Microsoft Windows [Version...│
│ C:\SIH>python main.py        │
│                              │
│ INITIALIZING TRIPLE MODEL... │
│ Loading: accident_v2.pt      │
│ Loading: ambulance.pt        │
│ Loading: damage.pt           │
│ ...                          │
│ Uvicorn running on port 8000 │
│ [Running...]                 │
└──────────────────────────────┘

Window 2: SIH-Frontend
┌──────────────────────────────┐
│ Microsoft Windows [Version...│
│ C:\SIH\dashboard>npm start   │
│                              │
│ > traffic-command-dashboard@│
│ > react-scripts start        │
│                              │
│ Compiled successfully!       │
│ Local: http://localhost:3000 │
│ [Running...]                 │
└──────────────────────────────┘

Window 3: Browser
┌──────────────────────────────┐
│ TRAFFIC COMMAND: INDIA GRID  │
│                              │
│ Status: Connected            │
│                              │
│ [Dashboard UI appears here]  │
└──────────────────────────────┘
```

**Step 5: Use Your Dashboard**
- Select Algorithm
- Choose Junction Type
- View Live Data
- Click Test Buttons

**Step 6: Shutdown**
- Close the two terminal windows
- Or wait for main window prompt

---

## DETAILED STEP-BY-STEP: Using python start_system.py

### For Users Familiar with PowerShell

**Step 1: Open PowerShell**
```
Press: Windows Key + X
Select: PowerShell (Admin) or PowerShell
```

**Step 2: Navigate to Folder**
```powershell
cd c:\SIH
```

**Step 3: Run the Script**
```powershell
python start_system.py
```

**Step 4: Watch the Output**
```
============================================================
      *** CODING_NEXUS LAUNCH PROTOCOL (SIH 2025) ***
============================================================

[1/3] Initializing AI Core...
      (Virtual Env not found. Falling back to System Python)

[2/3] Waiting for AI Core to respond...
      (Attempt 1/20...)
      (Attempt 2/20...)
      (Attempt 3/20...)
      (Attempt 4/20...)
      (AI Core is online!)

[3/3] Launching Command Dashboard...
      Frontend process started...

[+] Opening browser...

============================================================
    SYSTEM IS LIVE. Press Enter here to shut down all services.
============================================================
```

**Step 5: Use Your Dashboard**
- Dashboard opens automatically
- Play with the system

**Step 6: Shutdown**
- Press Enter in PowerShell
- Script will cleanly close everything
- All processes terminate

---

## WHAT HAPPENS INSIDE EACH STARTUP METHOD

### START_SYSTEM.bat Flow
```
Double-Click
    ↓
Check files exist
    ↓
Spawn Backend Process (new window)
    ├─ cd c:\SIH
    └─ python main.py
    ↓
Wait 3 seconds
    ↓
Spawn Frontend Process (new window)
    ├─ cd c:\SIH\dashboard
    └─ npm start
    ↓
Wait 6 seconds (React compilation)
    ↓
Open Browser
    └─ http://localhost:3000
    ↓
Wait for windows to close
```

### python start_system.py Flow
```
Run Script
    ↓
[1/3] Start Backend Process (separate console)
    └─ subprocess.Popen(python main.py)
    ↓
[2/3] Health Check Loop (max 20 attempts)
    └─ Query http://localhost:8000/docs
       ├─ Attempt 1: Waiting...
       ├─ Attempt 2: Waiting...
       ├─ Attempt 3: Waiting...
       └─ Attempt 4: Success!
    ↓
[3/3] Start Frontend Process (separate console)
    └─ subprocess.Popen(npm start)
    ↓
Wait 5 seconds
    ↓
Open Browser
    └─ http://localhost:3000
    ↓
Display message: "Press Enter to shut down"
    ↓
[User presses Enter]
    ↓
Terminate all processes using taskkill
    ├─ taskkill /F /T /PID <backend_pid>
    └─ taskkill /F /T /PID <frontend_pid>
    ↓
Script ends
```

### Manual 3-Terminal Flow
```
Terminal 1: cd c:\SIH && python main.py
    └─ Backend loads (manual monitoring)

Terminal 2: cd c:\SIH\dashboard && npm start
    └─ Frontend loads (manual monitoring)

Terminal 3: Open http://localhost:3000
    └─ Browser shows dashboard

Manual Shutdown:
    Terminal 1: Ctrl+C
    Terminal 2: Ctrl+C
    Browser: Close tab
```

---

## EXPECTED CONSOLE OUTPUT

### Backend (Python/FastAPI)
```
INITIALIZING TRIPLE MODEL SYSTEM - HIGH ACCURACY MODE
Checking models in: c:\SIH\backend\models\
OK [MODEL 1] Vehicle Detection: accident_v2.pt
   Classes: ['fire', 'smoke', 'minor_accident', 'severe_accident']
OK [MODEL 2] Ambulance Detection: ambulance.pt
   Classes: ['Ambulance']
OK [MODEL 3] Damage Severity: damage.pt (Classification)
   Classes: ['Minor', 'Minor Moderate', 'Moderate', 'Severe', 'Unlabeled']
ALL MODELS LOADED - SYSTEM READY
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Frontend (React/npm)
```
> traffic-command-dashboard@1.0.0 start
> react-scripts start

(node:12345) [DEP0176] DeprecationWarning: ...
Compiled successfully!

You can now view traffic-command-dashboard in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://10.125.48.116:3000

webpack compiled successfully
```

### Browser Dashboard
```
Status: Connected (Green badge)
Algorithm: Adaptive Timing
Junction Type: 4-Way
GPS: [locked when data arrives]
Signals: NORTH(RED), EAST(RED), SOUTH(RED), WEST(RED)
Traffic Level: 0-100% (based on AI detection)
```

---

## TROUBLESHOOTING QUICK REFERENCE

### Problem: "Port 8000 already in use"
**Solution:**
```powershell
taskkill /F /IM python.exe
python start_system.py
```

### Problem: "Port 3000 already in use"
**Solution:**
```powershell
taskkill /F /IM node.exe
python start_system.py
```

### Problem: "npm start fails"
**Solution:**
```powershell
cd c:\SIH\dashboard
npm install
npm start
```

### Problem: "main.py not found"
**Solution:**
- Make sure you're in `c:\SIH`
- Check that `main.py` exists there
- Run from `c:\SIH` directory

### Problem: "Backend won't load"
**Solution:**
```powershell
cd c:\SIH
python main.py
# Check for errors in the output
```

### Problem: "Browser won't open"
**Solution:**
- Manually open http://localhost:3000
- Check if React compiled (should say "Compiled successfully!")
- Wait longer for React to finish

### Problem: "Models not found"
**Solution:**
```powershell
Test-Path c:\SIH\backend\models\*.pt
# Should show True for all model files
```

---

## QUICK DECISION TREE

```
Do you prefer:
    │
    ├─ Clicking things? → Use START_SYSTEM.bat
    │
    ├─ Command line but want auto-shutdown? → Use python start_system.py
    │
    └─ Full control + debugging? → Use manual 3-terminal method
```

---

## RECOMMENDED WORKFLOW

1. **First Time Setup:**
   ```powershell
   cd c:\SIH\dashboard
   npm install
   # Then use START_SYSTEM.bat
   ```

2. **Daily Usage:**
   ```
   Double-click START_SYSTEM.bat
   Use dashboard
   Close windows when done
   ```

3. **Debugging:**
   ```powershell
   # Terminal 1
   cd c:\SIH
   python main.py
   
   # Terminal 2
   cd c:\SIH\dashboard
   npm start
   
   # Check console output for errors
   ```

---

## FILES YOU NEED TO KNOW ABOUT

| File | Location | Purpose |
|------|----------|---------|
| **START_SYSTEM.bat** | `c:\SIH\` | One-click startup (Windows) |
| **start_system.py** | `c:\SIH\` | One-click startup (Python) |
| **main.py** | `c:\SIH\` | Backend server |
| **package.json** | `c:\SIH\dashboard\` | Frontend dependencies |
| **npm start** | Run from `dashboard\` | Start frontend |

---

## YOU'RE READY!

**Easiest:** Double-click `START_SYSTEM.bat`

**That's it!** Your complete Smart Intelligent Highways system will launch in about 30 seconds.

Enjoy!
