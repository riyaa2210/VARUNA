# STARTUP OPTIONS - FINAL SUMMARY

## Option 1: WINDOWS BATCH FILE (ABSOLUTE EASIEST)

### Location
```
C:\SIH\START_SYSTEM.bat
```

### How to Use
1. Open Windows Explorer
2. Go to `C:\SIH`
3. Find `START_SYSTEM.bat`
4. **Double-click it**
5. Done! Watch 2 terminal windows open automatically

### What It Does
- Starts Backend (port 8000)
- Waits for it to be ready
- Starts Frontend (port 3000)
- Opens browser automatically
- You just watch and use it

### To Stop
- Close the Backend window
- Close the Frontend window

### Time to Live
~30 seconds

---

## Option 2: PYTHON SCRIPT (RECOMMENDED)

### Command
```powershell
cd c:\SIH
python start_system.py
```

### How to Use
1. Open PowerShell at `C:\SIH`
2. Run the command above
3. Watch the startup happen
4. Dashboard opens automatically
5. **Press Enter to stop everything**

### What It Does
- Starts Backend (port 8000)
- Checks if it's responding (health check)
- Starts Frontend (port 3000)
- Opens browser
- Handles clean shutdown

### Why It's Better
- Automatic health checking
- Clean shutdown (press Enter)
- No manual process termination needed
- Works on any OS with Python

### Time to Live
~30 seconds

---

## Option 3: MANUAL (FOR DEBUGGING)

### Terminal 1 - Backend
```powershell
cd c:\SIH
python main.py
```

### Terminal 2 - Frontend
```powershell
cd c:\SIH\dashboard
npm start
```

### Terminal 3 - Browser
```
Open: http://localhost:3000
```

### How to Stop
- Terminal 1: `Ctrl+C`
- Terminal 2: `Ctrl+C`
- Browser: Close tab

### Why Use This
- See real-time logs from both services
- Can restart individual services
- Better for debugging
- More control

### Time to Live
~30 seconds

---

## COMPARISON TABLE

| Feature | Batch File | Python Script | Manual |
|---------|-----------|---------------|--------|
| Easiest | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| Best for Everyone | ✓ | ✓ | - |
| Auto Health Check | ✗ | ✓ | ✗ |
| Auto Shutdown | ✗ | ✓ | ✗ |
| Debugging | ✗ | - | ✓ |
| Time to Start | ~30s | ~30s | ~30s |

---

## WHICH ONE SHOULD YOU CHOOSE?

### Choose Batch File If:
- You're on Windows
- You want the absolute simplest option
- You don't like command lines
- You just want to click and go

### Choose Python Script If:
- You know how to use PowerShell
- You want health checking
- You want clean shutdown with Enter key
- You want the most reliable option

### Choose Manual If:
- You're a developer
- You need to debug something
- You want to monitor both services
- You want full control

---

## QUICK CHECKLIST

Before starting, verify:
- [ ] You have `C:\SIH\START_SYSTEM.bat` OR
- [ ] You can run `python start_system.py` OR
- [ ] You have 2 PowerShell windows ready

Check that files exist:
- [ ] `C:\SIH\main.py` (backend)
- [ ] `C:\SIH\dashboard\package.json` (frontend)
- [ ] `C:\SIH\backend\models\*.pt` (AI models)

---

## EXPECTED OUTPUT

### Backend (Should Show)
```
INITIALIZING TRIPLE MODEL SYSTEM - HIGH ACCURACY MODE
OK [MODEL 1] Vehicle Detection: accident_v2.pt
OK [MODEL 2] Ambulance Detection: ambulance.pt
OK [MODEL 3] Damage Severity: damage.pt
ALL MODELS LOADED - SYSTEM READY
Uvicorn running on http://0.0.0.0:8000
Application startup complete
```

### Frontend (Should Show)
```
Compiled successfully!

You can now view traffic-command-dashboard in the browser.
Local: http://localhost:3000
webpack compiled successfully
```

### Browser (Should Show)
```
TRAFFIC COMMAND: INDIA GRID
Status: Connected ✓
Algorithm: Adaptive
Junction Type: 4-Way
Live Data: Ready
```

---

## TROUBLESHOOTING

### Issue: "Port 8000 already in use"
```powershell
taskkill /F /IM python.exe
# Then try again
```

### Issue: "Port 3000 already in use"
```powershell
taskkill /F /IM node.exe
# Then try again
```

### Issue: "npm start fails"
```powershell
cd c:\SIH\dashboard
npm install
npm start
```

### Issue: "main.py not found"
- Make sure you're in `C:\SIH`
- Check file exists: `Test-Path c:\SIH\main.py`

### Issue: "Can't find START_SYSTEM.bat"
- It's at: `C:\SIH\START_SYSTEM.bat`
- If missing, ask to recreate it

---

## PORTS TO KNOW

| Service | Port | URL |
|---------|------|-----|
| Backend | 8000 | http://localhost:8000 |
| Frontend | 3000 | http://localhost:3000 |
| WebSocket | 8000 | ws://localhost:8000/ws |

---

## FILES OVERVIEW

```
C:\SIH\
├── START_SYSTEM.bat          ← Use this (option 1)
├── start_system.py           ← Use this (option 2)
├── main.py                   ← Backend (starts automatically)
├── signal_algorithms.py      ← Algorithms (loaded by main.py)
├── backend/models/           ← AI Models
│   ├── accident_v2.pt
│   ├── ambulance.pt
│   ├── damage.pt
│   └── yolov8n.pt
├── dashboard/                ← Frontend (starts automatically)
│   ├── package.json
│   ├── public/
│   ├── src/
│   └── node_modules/
├── data/evidence_archive/    ← Evidence storage
├── archives/backup-code/     ← Old code backups
└── Documentation/
    ├── HOW_TO_START.md
    ├── STARTUP_MANUAL.md
    ├── QUICK_START_GUIDE.md
    └── ...
```

---

## WHAT EACH OPTION DOES STEP BY STEP

### Batch File Process
```
1. Double-click START_SYSTEM.bat
   ↓
2. PowerShell opens
   ↓
3. Batch script runs
   ↓
4. Checks if main.py exists
   ↓
5. Spawns Backend process (new console)
   ↓
6. Waits 3 seconds
   ↓
7. Spawns Frontend process (new console)
   ↓
8. Waits 6 seconds
   ↓
9. Opens http://localhost:3000 in browser
   ↓
10. You can now use the dashboard
```

### Python Script Process
```
1. Type: python start_system.py
   ↓
2. Script starts
   ↓
3. Spawns Backend process (separate window)
   ↓
4. Health check loop starts (queries localhost:8000)
   ↓
5. Waits up to 20 seconds for backend response
   ↓
6. Backend responds ✓
   ↓
7. Spawns Frontend process (separate window)
   ↓
8. Waits 5 seconds for React to compile
   ↓
9. Opens http://localhost:3000 in browser
   ↓
10. Shows: "Press Enter to shut down"
   ↓
11. User presses Enter
   ↓
12. Script terminates all processes cleanly
   ↓
13. Script ends
```

### Manual Process
```
1. Open Terminal 1 → cd c:\SIH → python main.py
   ↓
   (Wait for "Uvicorn running on http://0.0.0.0:8000")

2. Open Terminal 2 → cd c:\SIH\dashboard → npm start
   ↓
   (Wait for "Compiled successfully!")

3. Open Browser → http://localhost:3000
   ↓
   (Dashboard loads)

4. Use the system

5. To stop:
   - Terminal 1: Ctrl+C
   - Terminal 2: Ctrl+C
```

---

## FINAL RECOMMENDATION

**For 99% of users:**
```powershell
cd c:\SIH
python start_system.py
```

**For Windows users who want no commands:**
```
Double-click C:\SIH\START_SYSTEM.bat
```

**For developers:**
```
Use manual 3-terminal method
```

---

## YOU'RE READY!

Pick one option above and launch your Smart Intelligent Highways system!

All systems are configured and ready to go. No further setup needed.
