@echo off
REM Simple batch script to run SIH video analysis

setlocal enabledelayedexpansion

set VENV_PYTHON=C:\Users\sharm\Downloads\SIH-20251206T045351Z-3-001\.venv\Scripts\python.exe
set SIH_DIR=C:\Users\sharm\Downloads\SIH-20251206T045351Z-3-001\SIH-20251206T045351Z-3-001\SIH

echo.
echo ============================================
echo  🎬 VIDEO ANALYSIS STARTUP
echo ============================================
echo.
echo Installing dependencies...
%VENV_PYTHON% -m pip install --upgrade opencv-python fastapi uvicorn pydantic requests websockets ultralytics torch torchvision -q

echo ✅ Dependencies ready!
echo.
echo Starting SIH Backend...
echo Input: video.mp4
echo Port: 8888
echo.
echo Press Ctrl+C to stop.
echo.

cd /d "%SIH_DIR%"
%VENV_PYTHON% main.py

pause
