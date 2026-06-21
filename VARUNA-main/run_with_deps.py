#!/usr/bin/env python3
"""
Smart Intelligent Highways - Backend Launcher with Dependency Check
This script ensures all dependencies are installed before starting the backend.
"""

import subprocess
import sys
import os

# Add current directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🚦 Backend Startup - Dependency Check")
print("=" * 60)

# List of required packages
REQUIRED_PACKAGES = {
    'cv2': 'opencv-python',
    'fastapi': 'fastapi',
    'uvicorn': 'uvicorn',
    'ultralytics': 'ultralytics',
    'pydantic': 'pydantic',
    'requests': 'requests',
    'websockets': 'websockets',
}

missing_packages = []

# Check each package
print("\n📦 Checking dependencies...")
for import_name, pip_name in REQUIRED_PACKAGES.items():
    try:
        __import__(import_name)
        print(f"  ✅ {import_name}")
    except ImportError:
        print(f"  ❌ {import_name} - MISSING")
        missing_packages.append(pip_name)

# Install missing packages
if missing_packages:
    print(f"\n⚙️  Installing {len(missing_packages)} missing package(s)...")
    cmd = [sys.executable, '-m', 'pip', 'install'] + missing_packages
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"❌ Failed to install packages!")
        sys.exit(1)
    print("✅ All packages installed successfully!")
else:
    print("\n✅ All dependencies are already installed!")

# Now import and check YOLO specifically
print("\n🤖 Checking YOLO Detection System...")
try:
    from ultralytics import YOLO
    print("  ✅ YOLO Available")

    # Try to load the model
    model_path = os.path.join(os.path.dirname(__file__), 'backend', 'models', 'accident_v2.pt')
    if os.path.exists(model_path):
        print(f"  ✅ Model file found: {model_path}")
    else:
        print(f"  ⚠️  Model file not found: {model_path}")
except Exception as e:
    print(f"  ❌ YOLO Error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print(" 🚀 Starting Backend Server on port 8080...")
print("=" * 60 + "\n")

# Start the main application
try:
    import main
except Exception as e:
    print(f"ERROR starting main: {e}")
    sys.exit(1)
