# 🚦 VARUNA

### AI-Powered Real-Time Traffic & Incident Management System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Computer%20Vision-orange?style=for-the-badge)
![OpenCV](https://img.shields.io/badge/OpenCV-Image%20Processing-green?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge)
![React](https://img.shields.io/badge/React-Dashboard-61DAFB?style=for-the-badge)

<br>

### 🧠 Real-Time Computer Vision • 🚦 Smart Traffic Control • 🚑 Emergency Response

*Detect. Decide. Respond.*

</div>

---

## 🎯 Overview

**VARUNA** is a full-stack AI-powered traffic surveillance and emergency response platform that continuously monitors road intersections using Computer Vision.

The system automatically:

✅ Detects accidents and fires in real time

✅ Validates incidents using temporal intelligence

✅ Optimizes traffic signals dynamically

✅ Creates emergency corridors

✅ Dispatches alerts with geo-tagged locations

✅ Routes responders to the nearest hospital

Built using **YOLOv8, OpenCV, PyTorch, FastAPI, React.js, WebSockets, and OSRM**.

---

## 🎥 Demo Workflow

```text
📹 Live Camera Feed
         │
         ▼
🧠 YOLOv8 Object Detection
         │
         ▼
🔍 Temporal Validation
 (12-Frame Majority Vote)
         │
         ▼
🚨 Incident Confirmation
         │
 ┌───────┼────────┐
 ▼       ▼        ▼
🚦      📱       📸
Signal  Alert    Evidence
Control Telegram Capture
         │
         ▼
🏥 Hospital Routing
         │
         ▼
🗺️ Live Dashboard Updates
```

---

## ✨ Key Features

### 🧠 Real-Time Computer Vision

* Accident detection using YOLOv8
* Fire detection with confidence filtering
* Vehicle detection and traffic density estimation
* Live video analytics from IP camera streams

### 🔒 False Positive Reduction

* 12-frame rolling majority voting
* Temporal event validation
* Stable incident confirmation before triggering alerts

### 🚦 Intelligent Traffic Signal Optimization

Supports:

* 2-Way Junctions
* 3-Way Junctions
* 4-Way Junctions
* 5-Way Junctions
* 6-Way Junctions

Traffic signals adapt automatically based on:

* Traffic load
* Accident severity
* Fire emergencies
* Emergency vehicle movement

### 🚑 Automated Emergency Response

Upon incident detection:

* Evidence frame captured
* Telegram alert generated
* Location pin shared
* Nearest hospital identified
* Optimal route calculated
* ETA displayed in dashboard

---

## 🏗️ System Architecture

```text
                ┌──────────────────────┐
                │   Live Camera Feed   │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ YOLOv8 Detection     │
                │ OpenCV Processing    │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Temporal Validation  │
                │ 12-Frame Voting      │
                └──────────┬───────────┘
                           │
                ┌──────────┼───────────┐
                ▼          ▼           ▼

         🚦 Signal     📱 Alert      📸 Evidence
          Engine      System        Capture

                └──────────┬───────────┘
                           ▼

                 🏥 Emergency Routing
                           │
                           ▼

                 🌐 React Dashboard
```

---

## 🛠️ Tech Stack

### Computer Vision & AI

| Technology      | Purpose            |
| --------------- | ------------------ |
| YOLOv8          | Object Detection   |
| OpenCV          | Image Processing   |
| PyTorch         | Deep Learning      |
| Computer Vision | Incident Detection |

---

### Backend

| Technology | Purpose                 |
| ---------- | ----------------------- |
| FastAPI    | API Layer               |
| WebSockets | Real-Time Communication |
| Uvicorn    | ASGI Server             |
| Python     | Core Logic              |

---

### Frontend

| Technology     | Purpose             |
| -------------- | ------------------- |
| React.js       | Dashboard           |
| Leaflet.js     | Interactive Maps    |
| Web Speech API | Voice Announcements |

---

### Integrations

| Technology        | Purpose            |
| ----------------- | ------------------ |
| Telegram Bot API  | Incident Alerts    |
| OSRM              | Route Optimization |
| IP Camera Streams | Live Video Source  |

---

## 🚀 Core Innovations

### 1️⃣ Temporal Incident Validation

Most surveillance systems trigger alerts from a single frame.

VARUNA validates incidents across **12 consecutive frames** before taking action.

Benefits:

* Reduced false positives
* More reliable alerts
* Improved system stability

---

### 2️⃣ Adaptive Signal Intelligence

The system dynamically changes signal timings based on:

* Traffic density
* Accidents
* Fire emergencies
* Multi-lane congestion

Creating safer and faster traffic flow.

---

### 3️⃣ Automated Emergency Routing

Emergency responders receive:

* Incident image
* Severity level
* GPS location
* Nearest hospital route
* Estimated arrival time

Within seconds of confirmation.

---

## 📊 Project Highlights

| Metric              | Value        |
| ------------------- | ------------ |
| Detection Engine    | YOLOv8       |
| Incident Validation | 12 Frames    |
| Supported Junctions | 2–6 Way      |
| Alert System        | Telegram Bot |
| Routing Engine      | OSRM         |
| Communication       | WebSockets   |
| Dashboard           | React.js     |
| Backend             | FastAPI      |

---

## 📂 Project Structure

```text
VARUNA/
│
├── backend/
│   ├── main.py
│   ├── signal_algorithms.py
│
├── dashboard/
│   ├── src/
│   └── public/
│
├── models/
│
├── evidence_archive/
│
├── start_system.py
│
└── requirements.txt
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/riyaa2210/VARUNA.git
cd VARUNA
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Application

```bash
python start_system.py
```

Dashboard:

```text
http://localhost:3000
```

---

## 🔮 Future Enhancements

* Multi-camera traffic monitoring
* Automatic Number Plate Recognition (ANPR)
* Ambulance detection and prioritization
* Edge deployment on Jetson Nano
* Historical analytics dashboard
* Smart city integration

---

## 👩‍💻 Author

### Riya D. Ransing

AI/ML • Computer Vision • Full-Stack Development

GitHub: https://github.com/riyaa2210

LinkedIn: https://www.linkedin.com/in/riya-ransing-86607a318

---

<div align="center">

### ⭐ If you found this project interesting, consider starring the repository!

**Built with Computer Vision, AI, and a passion for smarter cities 🚦**

</div>
