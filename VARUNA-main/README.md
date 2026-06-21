<div align="center">

# 🚦 VARUNA
### AI-Powered Real-Time Traffic & Incident Management System

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-FF6B35?style=for-the-badge)](https://ultralytics.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<br/>

> **Built for Smart India Hackathon 2025** — An end-to-end AI system that watches intersections 24/7, detects accidents and fires in real time, controls traffic signals intelligently, and dispatches emergency responders — all autonomously.

<br/>

![VARUNA Dashboard Preview](https://img.shields.io/badge/Dashboard-Live%20Demo-brightgreen?style=flat-square)
![Detection](https://img.shields.io/badge/Detection-YOLOv8%20Custom%20Model-orange?style=flat-square)
![Alerts](https://img.shields.io/badge/Alerts-Telegram%20Bot-blue?style=flat-square)

</div>

---

## 🎯 What Does VARUNA Do?

VARUNA is a full-stack, production-ready intelligent traffic system that runs on a single machine and a phone camera. It:

- 🔍 **Detects** accidents, fires, and vehicle congestion in real time using a custom-trained YOLOv8 model
- 🚦 **Controls** traffic signals automatically using 5 intelligent algorithms that adapt to incidents
- 📸 **Archives** timestamped evidence photos of every detected incident with bounding box overlays
- 📱 **Alerts** emergency services via Telegram with the incident photo + GPS location pin in seconds
- 🗺️ **Routes** the nearest hospital on a live interactive map using real road data (OSRM)
- 🔊 **Announces** alerts via browser voice synthesis (Web Speech API)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        VARUNA SYSTEM                            │
│                                                                 │
│  📱 Phone Camera (IP Webcam App)                                │
│         │  MJPEG Stream over Wi-Fi                              │
│         ▼                                                       │
│  ┌─────────────────────────────────────┐                        │
│  │      Python Backend (main.py)       │                        │
│  │                                     │                        │
│  │  VideoStream ──► YOLOv8 Detection  │                        │
│  │       │               │             │                        │
│  │  Frame Buffer    Confidence Filter  │                        │
│  │       │               │             │                        │
│  │  CLAHE Enhancement    │             │                        │
│  │       │         12-Frame Stabilizer │                        │
│  │       │               │             │                        │
│  │       │         Severity Classifier │                        │
│  │       │          /           \      │                        │
│  │  Evidence Capture    Signal Algo    │                        │
│  │  (Archive + Snap)   Controller     │                        │
│  │       │               │             │                        │
│  │  Telegram Alert    WebSocket Push  │                        │
│  └───────────────────────┬───────────┘                        │
│                           │                                     │
│  ┌────────────────────────▼───────────┐                        │
│  │     React Dashboard (App.js)       │                        │
│  │                                    │                        │
│  │  Live Feed │ Tactical Map │ Logic  │                        │
│  │  Signals   │ OSRM Route   │ Logs   │                        │
│  └────────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Key Features

### 🤖 AI Detection Pipeline
| Feature | Detail |
|---|---|
| Model | Custom YOLOv8 (`accident_v2.pt`) + YOLOv8n fallback |
| Detection Classes | `accident`, `fire`, `smoke`, `severe_accident`, `car`, `truck`, `bus`, `motorcycle` |
| Tracking | `model.track()` with persistent object IDs across frames |
| False Positive Filter | 12-frame rolling stabilizer with 60% majority vote threshold |
| Confidence Thresholds | Fire: 60% · Accident: 50% · Vehicle: 30% |
| Low-light Enhancement | CLAHE on LAB color space for night/indoor scenes |

### 🚦 Smart Signal Control (5 Algorithms)
| Priority | Scenario | Algorithm | Behavior |
|---|---|---|---|
| 1 | 🔥 Fire | Fire Evacuation | All safe lanes: 5s cycles, max throughput |
| 2 | 💥💥 Multiple Accidents | Multi-Accident | Single safe exit lane, 45s green, manual override alert |
| 3 | 💥 Single Accident | Accident Diversion | Opposite lane: 30s green, blocked lane skipped |
| 4 | 🚑 Emergency Vehicle | Green Corridor | Emergency direction: 60s solid green |
| 5 | 🚗 Normal Traffic | Adaptive | Low traffic → round-robin; High → weighted by vehicle count |

Supports **2-way through 6-way intersections** — switchable live from the dashboard.

### 📸 Evidence Capture System
- Every frame with a detection → saved to `evidence_archive/detected/` with annotations
- Confirmed incidents → saved to `evidence_archive/severe/` or `evidence_archive/fire/`
- Microsecond-precision timestamps: `detected_20260621_190056_836097.jpg`
- CLAHE-enhanced before saving for maximum clarity

### 📱 Telegram Alerting
- 30-second cooldown prevents spam
- Non-blocking background thread — never slows the video feed
- Message 1: Evidence photo + severity caption
- Message 2: GPS location pin (opens in Google Maps on tap)

### 🗺️ Emergency Routing
- Nearest hospital found via Euclidean distance from 6-hospital database
- Real road route drawn via [OSRM](https://project-osrm.org/) (no API key needed)
- Live ETA displayed on map
- Voice alert via Web Speech API

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Android phone with [IP Webcam](https://play.google.com/store/apps/details?id=com.pas.webcam) app (or use local webcam)

### 1. Clone the repo
```bash
git clone https://github.com/riyaa2210/VARUNA.git
cd VARUNA
```

### 2. Install Python dependencies
```bash
pip install fastapi uvicorn opencv-python ultralytics python-dotenv requests
```

Or use the installer:
```bash
install_deps.bat        # Windows
```

### 3. Configure your camera
Edit `main.py` line ~65 or set environment variable:
```bash
# Windows PowerShell
$env:MOBILE_CAMERA_URL = "http://YOUR_PHONE_IP:8080"

# Use local webcam instead:
# MOBILE_CAMERA_URL = 0
```

### 4. Set up Telegram alerts (optional)
```bash
$env:TELEGRAM_BOT_TOKEN = "your_bot_token"
$env:TELEGRAM_CHAT_ID   = "your_chat_id"
```

### 5. Launch everything
```bash
python start_system.py
```

This automatically:
- Starts the AI backend on `http://localhost:8000`
- Waits for backend health check to pass
- Starts React dashboard on `http://localhost:3000`
- Opens browser

> **One-click launch. Everything in one terminal.**

---

## 📁 Project Structure

```
VARUNA/
│
├── main.py                    # 🧠 Core backend — FastAPI + YOLO + WebSocket
├── signal_algorithms.py       # 🚦 5 signal control algorithms
├── start_system.py            # 🚀 One-click launcher
├── start_system.bat           # 🪟 Windows batch launcher
├── install_deps.bat           # 📦 Dependency installer
│
├── dashboard/                 # ⚛️  React frontend
│   ├── src/
│   │   ├── App.js             # Full dashboard UI (map, feed, signals, logs)
│   │   └── App.css            # Dark command-center styling
│   └── public/
│
├── backend/
│   └── models/
│       └── accident_v2.pt     # 🤖 Custom YOLOv8 model (gitignored — large file)
│
├── evidence_archive/          # 📸 Auto-generated incident evidence (gitignored)
│   ├── detected/              # All detection frames with annotations
│   ├── severe/                # Confirmed accident evidence
│   └── fire/                  # Confirmed fire evidence
│
├── test_fire_detection.py     # 🔥 Standalone fire detection test script
├── simulate_alert.py          # 🧪 Telegram alert simulator
├── diag_import.py             # 🔧 Dependency diagnostic tool
├── video.mp4                  # 🎬 Sample test video
└── IP_WEBCAM_SETUP.md         # 📖 Camera setup guide
```

---

## 🎮 Dashboard Controls

| Control | What It Does |
|---|---|
| Algorithm Dropdown | Switch between Adaptive / Zone Rotation / Weighted Priority |
| Junction Selector (2–6) | Change intersection type live — signal grid updates automatically |
| Traffic Load Sliders | Manually set vehicle counts for East / South / West lanes |
| SIMULATE CRASH | Drop a crash marker and trigger hospital routing |
| RESET SYSTEM | Clear all incidents, routes, and evidence display |
| Map Click | Manually place incident marker anywhere on the map |

---

## 🔌 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/ws` | WebSocket | Real-time frame + signal + incident stream |
| `/update-lanes` | POST | Update manual vehicle counts `{east, south, west}` |
| `/set-junction` | POST | Change junction type `{junction_type: 2-6}` |
| `/set-algorithm` | POST | Switch algorithm `{algorithm: "adaptive"\|"zone"\|"weighted"}` |
| `/reset-system` | POST | Clear all incident state |
| `/health` | GET | Backend + model status check |
| `/test-camera` | GET | Test camera connectivity |
| `/docs` | GET | Auto-generated Swagger UI |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **AI/Detection** | YOLOv8 (Ultralytics), OpenCV, CLAHE |
| **Backend** | Python, FastAPI, Uvicorn, WebSockets |
| **Frontend** | React.js, Leaflet.js, Web Speech API |
| **Alerts** | Telegram Bot API |
| **Routing** | OSRM (Open Source Routing Machine) |
| **Camera** | Android IP Webcam / OpenCV VideoCapture |
| **Data** | Python deque + Counter (no database needed) |

---

## 🧠 How the Detection Logic Works

```
Frame
 │
 ├─► YOLOv8 model.track()  ← conf=0.15 (intentionally low)
 │         │
 │    Per-box filter:
 │    - fire    → conf ≥ 0.60 AND box ≥ 20×20px
 │    - accident→ conf ≥ 0.50
 │    - vehicle → conf ≥ 0.30
 │         │
 │    Raw status: Fire > Accident > Minor > Traffic > Normal
 │         │
 └─► 12-frame Stabilizer (60% majority vote)
           │
      Confirmed status
      /              \
  mark_incident()    evidence saved
  signal algorithm   + Telegram alert
  switches           + hospital route
```

The stabilizer is the key innovation — it prevents a single blurry frame from triggering a city-wide emergency response.

---

## 📊 Performance

| Metric | Value |
|---|---|
| Detection latency | ~100–200ms per frame |
| Alert delivery | < 3 seconds (background thread) |
| WebSocket update rate | ~50 FPS (20ms interval) |
| False positive suppression | 12-frame / 60% vote |
| Alert cooldown | 30 seconds per incident type |
| Startup time | ~20–30 seconds (async model load) |

---

## 🔮 Roadmap

- [ ] GPS-based ambulance detection (IncidentLevel.AMBULANCE already scaffolded)
- [ ] Multi-camera support with unified incident map
- [ ] ANPR (Automatic Number Plate Recognition) for vehicle logging
- [ ] Edge deployment on Raspberry Pi / Jetson Nano
- [ ] WhatsApp alerting via Twilio
- [ ] Historical analytics dashboard with Pandas/Plotly

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first.

1. Fork the repo
2. Create your feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 👤 Author

**Riya** — [@riyaa2210](https://github.com/riyaa2210)

Built with 🔥 for Smart India Hackathon 2025

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">

**If this project helped you, drop a ⭐ — it means a lot.**

</div>
