# 🚦 VARUNA – Real-Time Computer Vision Traffic Management System

VARUNA is an AI-powered traffic surveillance and incident management system that uses Computer Vision to detect accidents, fires, and traffic congestion from live camera feeds. The system automatically adapts traffic signals, dispatches emergency alerts, and routes responders to the nearest hospital in real time.

## ✨ Key Features

- Real-time accident, fire, and vehicle detection using YOLOv8
- 12-frame temporal validation to reduce false positives
- Adaptive traffic signal optimization for 2–6 way intersections
- Automated incident evidence capture and archival
- Telegram alerts with geo-tagged incident locations
- Emergency responder routing using OSRM
- Live monitoring dashboard with React.js and WebSockets

---

## 🏗️ System Architecture

Camera Feed
↓
YOLOv8 Detection
↓
Temporal Validation (12 Frames)
↓
Incident Confirmation
↓
Signal Optimization + Alert Generation
↓
Hospital Routing + Dashboard Updates

---

## 🛠️ Tech Stack

### AI & Computer Vision
- YOLOv8
- OpenCV
- PyTorch

### Backend
- FastAPI
- WebSockets
- Uvicorn

### Frontend
- React.js
- Leaflet.js

### Integrations
- Telegram Bot API
- OSRM Routing Engine
- Web Speech API

---

## 🚀 How It Works

### 1. Incident Detection
Live video streams are processed using YOLOv8 to identify:
- Accidents
- Fires
- Vehicles
- Traffic Congestion

### 2. Temporal Validation
A 12-frame rolling majority vote validates detections before triggering actions, significantly reducing false alarms.

### 3. Intelligent Traffic Control
The system dynamically adjusts traffic signals using adaptive algorithms based on:
- Traffic density
- Accident locations
- Emergency scenarios

### 4. Emergency Response
Upon incident confirmation:
- Evidence image is saved
- Telegram alert is generated
- Nearest hospital is identified
- Route and ETA are displayed

---

## 📊 Project Highlights

- Real-time Computer Vision pipeline
- Multi-scenario traffic signal optimization
- Automated emergency response workflow
- End-to-end full-stack architecture
- Scalable FastAPI backend with WebSocket communication

---

## 📁 Project Structure

VARUNA/
├── backend/
├── dashboard/
├── models/
├── evidence_archive/
├── main.py
├── signal_algorithms.py
└── start_system.py

---

## ⚙️ Installation
Clone Repository
git clone https://github.com/riyaa2210/VARUNA.git
cd VARUNA
pip install -r requirements.txt
python start_system.py
---

## 🎯 Future Enhancements
Multi-camera support
Automatic Number Plate Recognition (ANPR)
Edge deployment on Jetson Nano
Historical analytics dashboard
Ambulance detection and prioritization
---
