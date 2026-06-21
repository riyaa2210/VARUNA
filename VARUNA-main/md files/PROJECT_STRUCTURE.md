# SIH Project Structure

Professional organization of the Smart Intelligent Highways system with separated backend, frontend, archives, and data.

```
c:\SIH\
│
├─ 📂 BACKEND (Python + FastAPI)
│  ├─ main.py                          # FastAPI server (port 8000)
│  ├─ signal_algorithms.py             # Smart signal control algorithms
│  ├─ start_system.py                  # System startup script
│  │
│  └─ 📂 models/                       # AI Models (YOLO)
│     ├─ accident_v2.pt                # Vehicle detection (fire, smoke, accidents)
│     ├─ ambulance.pt                  # Ambulance detection
│     ├─ damage.pt                     # Damage severity classification
│     └─ yolov8n.pt                    # Fallback detection model
│
├─ 📂 FRONTEND (React Dashboard)
│  ├─ 📂 dashboard/
│  │  ├─ public/
│  │  │  ├─ index.html
│  │  │  ├─ manifest.json
│  │  │  └─ robots.txt
│  │  │
│  │  ├─ src/
│  │  │  ├─ App.js                     # Main React component
│  │  │  ├─ App.css                    # Styling
│  │  │  ├─ index.js                   # React entry point
│  │  │  ├─ index.css                  # Global styles
│  │  │  └─ setupTests.js
│  │  │
│  │  ├─ package.json
│  │  └─ README.md
│  │
│  └─ 📂 node_modules/                 # NPM dependencies
│
├─ 📂 DATA (Evidence & Archives)
│  └─ 📂 evidence_archive/
│     ├─ 📂 minor/                     # Minor accident evidence
│     ├─ 📂 moderate/                  # Moderate accident evidence
│     └─ 📂 severe/                    # Severe accident evidence
│
├─ 📂 ARCHIVES (Backup & Old Code)
│  └─ 📂 backup-code/
│     ├─ main.py.bak                   # Previous main.py versions
│     ├─ main_old_backup.py
│     ├─ main_rough.py
│     │
│     └─ 📂 old-trials/                # Experimental versions
│        ├─ Try_1/
│        ├─ Try_2/
│        ├─ Try_3/
│        ├─ Try_4/
│        └─ Try_5/
│
├─ 📄 Documentation Files
│  ├─ PROJECT_STRUCTURE.md             # This file
│  ├─ README_FINAL_ANSWER.md           # Complete system documentation
│  ├─ QUICK_START.md                   # Quick setup guide
│  ├─ DEPLOYMENT_SUMMARY.md            # Deployment details
│  ├─ INTEGRATION_GUIDE.md             # Integration instructions
│  ├─ FILE_COMPATIBILITY.md            # Component compatibility info
│  └─ ANSWER_TO_YOUR_QUESTION.md       # Feature documentation
│
└─ 🔧 System Files
   └─ (Python .venv or virtual environment)
```

## Quick Navigation

### Starting the System

**Backend (FastAPI + YOLO):**
```bash
cd c:\SIH
python main.py
```

**Frontend (React Dashboard):**
```bash
cd c:\SIH\frontend\dashboard
npm start
```

### Model Paths (Updated)
- Vehicle Detection: `backend/models/accident_v2.pt`
- Ambulance Detection: `backend/models/ambulance.pt`
- Damage Classification: `backend/models/damage.pt`
- Evidence Storage: `data/evidence_archive/`

### Backend Architecture
- **Server**: FastAPI on `http://0.0.0.0:8000`
- **WebSocket**: `ws://localhost:8000/ws`
- **Routes**:
  - `POST /update-lanes` - Manual lane traffic data
  - `POST /set-junction` - Change junction type (2-6 way)
  - `POST /set-algorithm` - Select algorithm (adaptive, zone, weighted)

### Frontend Architecture
- **React** components with WebSocket integration
- **Algorithm Selector** dropdown
- **Junction Type** selector
- **Live Video Feed** with synthetic fallback
- **Signal Grid** showing real-time signal states
- **Emergency Timer** countdown display
- **Emergency Playbook** incident visualization

## Key Features

### 1. Triple AI Model System
- **Vehicle Detection** (accident_v2.pt): Detects fire, smoke, minor accidents, severe accidents
- **Ambulance Detection** (ambulance.pt): Priority emergency response detection
- **Damage Classification** (damage.pt): Assesses severity (Minor/Moderate/Severe)

### 2. Multi-Route Signal Algorithms
1. **Adaptive**: Dynamically adjusts based on real-time traffic
2. **Zone**: Predefined time zones for signal cycles
3. **Weighted**: Priority-based signal allocation
4. **Emergency Corridor**: Emergency vehicle detection override
5. **Multi-Accident**: Manages multiple incident zones

### 3. Judge Dashboard Features
- Real-time timer with countdown
- Emergency playbook visualization
- Per-lane signal grid status
- Algorithm and junction type controls
- Live incident detection results

### 4. Robust Error Handling
- Non-blocking Telegram alerts via threading
- Model fallbacks (if custom models fail, use yolov8n)
- Synthetic video fallback when camera unavailable
- WebSocket resilience and reconnection

## File Sizes & Model Performance

| Model | Size | Classes | Method |
|-------|------|---------|--------|
| accident_v2.pt | 6.2 MB | 4 | `.track()` (Detection) |
| ambulance.pt | 6.2 MB | 1 | `.track()` (Detection) |
| damage.pt | 3.0 MB | 5 | `.predict()` (Classification) |
| yolov8n.pt | 6.5 MB | 80 | Fallback Detection |

## Separated Concerns

| Component | Location | Purpose |
|-----------|----------|---------|
| Backend Logic | `/backend/` | Core AI inference & signal control |
| Frontend UI | `/frontend/dashboard/` | React dashboard for judges |
| Models | `/backend/models/` | Pre-trained YOLO weights |
| Evidence | `/data/evidence_archive/` | Incident proof & media |
| Old Code | `/archives/backup-code/` | Experimental & legacy versions |

## Important Notes

1. **Model Paths**: All YOLO models now reference `backend/models/` - make sure to run main.py from project root
2. **Frontend Dependencies**: Navigate to `frontend/dashboard/` before running `npm start`
3. **Evidence Storage**: Automatically organized by severity (minor/moderate/severe)
4. **Backup Code**: Old trials preserved in `archives/backup-code/old-trials/` for reference

---

**Status**: ✅ Production Ready  
**Last Updated**: December 5, 2025  
**Version**: 1.0 (Triple Model System)
