# 🎯 MASTER QUICK REFERENCE

**Your SIH project is now professionally organized!**

---

## ⚡ ULTRA-QUICK START (30 seconds)

```bash
# Terminal 1: Start Backend
cd c:\SIH
python main.py

# Terminal 2: Start Frontend
cd c:\SIH\frontend\dashboard
npm start

# Browser: Open dashboard
http://localhost:3000
```

**That's it! System is running.**

---

## 📚 What to Read

| When | Read |
|------|------|
| First time? | **START_HERE.md** |
| Want details? | **FOLDER_GUIDE.md** |
| Want to understand structure? | **PROJECT_STRUCTURE.md** |
| Want before/after? | **ORGANIZATION_SUMMARY.md** |

---

## 📁 Key Folders

```
/              ← Python files here (main.py, etc)
/backend/models/       ← AI models (4 YOLO weights)
/frontend/dashboard/   ← React web app
/data/evidence_archive/← Incident evidence (auto-organized)
/archives/backup-code/ ← Old code (reference only)
```

---

## 🚀 System Runs On

- **Backend**: `http://localhost:8000` (FastAPI)
- **Frontend**: `http://localhost:3000` (React)
- **WebSocket**: `ws://localhost:8000/ws`

---

## 🎮 Using Dashboard

1. Select **Algorithm** (Adaptive/Zone/Weighted)
2. Select **Junction Type** (2-6 way)
3. Watch **Timer** countdown
4. See **Signal Grid** update
5. Evidence saved to `/data/evidence_archive/`

---

## 🔄 What's Inside

### Backend
- 3 YOLO detection/classification models running in parallel
- 5 signal control algorithms
- Telegram alerts for incidents
- Evidence auto-archiving by severity

### Frontend
- Real-time video feed (with synthetic fallback)
- Algorithm selector
- Junction type selector
- Timer display
- Signal grid status
- Emergency playbook

---

## ⚠️ Remember

✅ Run `python main.py` from **c:\SIH** root  
✅ Run `npm start` from **c:\SIH\frontend\dashboard**  
✅ Models reference **backend/models/** (already updated)  
✅ Evidence stored in **data/evidence_archive/** (auto-organized)  
✅ Old code in **archives/** (don't use - for reference)

---

## 🎯 Main Files

| File | Location | Purpose |
|------|----------|---------|
| main.py | `/` | FastAPI server |
| signal_algorithms.py | `/` | Smart signals |
| start_system.py | `/` | Launcher script |
| App.js | `/frontend/dashboard/src/` | React dashboard |

---

## ✨ You're All Set!

Your project is:
- ✅ **Clean** - Professional structure
- ✅ **Organized** - Everything in its place
- ✅ **Updated** - File paths corrected
- ✅ **Documented** - 4 guides created
- ✅ **Ready** - No changes needed

**Start coding!** 🚀

---

**Need more help?** Open **START_HERE.md**
