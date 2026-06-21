@echo off
setlocal enabledelayedexpansion

set VENV_PYTHON="C:\Users\sharm\Downloads\SIH-20251206T045351Z-3-001\.venv\Scripts\python.exe"

echo Installing dependencies...
%VENV_PYTHON% -m pip install opencv-python fastapi uvicorn pydantic requests websockets ultralytics torch torchvision -q

echo.
echo ✅ All dependencies installed!
echo.
pause
