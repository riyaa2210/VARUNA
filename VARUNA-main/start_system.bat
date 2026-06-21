@echo off
REM ========================================================================
REM   SMART INTELLIGENT HIGHWAYS - ONE-CLICK STARTUP
REM   Team: CODING_NEXUS | SIH 2025
REM ========================================================================

cls
color 0A
echo.
echo ========================================================================
echo.
echo   SMART INTELLIGENT HIGHWAYS - LAUNCH SEQUENCE
echo.
echo   Starting: Backend AI Core + Frontend Dashboard
echo.
echo ========================================================================
echo.

cd /d c:\SIH

REM ========================================================================
REM   CHECK IF FILES EXIST
REM ========================================================================

if not exist "main.py" (
    echo [ERROR] main.py not found in c:\SIH
    pause
    exit /b 1
)

if not exist "dashboard" (
    echo [ERROR] dashboard folder not found in c:\SIH
    pause
    exit /b 1
)

REM ========================================================================
REM   CHECK FOR PYTHON VIRTUAL ENVIRONMENT
REM ========================================================================

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Python virtual environment not found in c:\SIH\venv
    echo [INFO]  Please create it using: python -m venv venv
    echo [INFO]  Then install dependencies: venv\Scripts\pip.exe install -r requirements.txt
    pause
    exit /b 1
)

REM ========================================================================
REM   START BACKEND SERVER (Port 8000)
REM ========================================================================

echo [1/3] Starting AI Core (FastAPI + YOLO Models)...
echo        Port: 8000
echo        Status: Loading...

start "SIH-Backend" cmd /k venv\Scripts\python.exe main.py

timeout /t 3 /nobreak

REM ========================================================================
REM   START FRONTEND DASHBOARD (Port 3000)
REM ========================================================================

echo [2/3] Starting Command Dashboard (React App)...
echo        Port: 3000
echo        Status: Compiling...
echo.

start "SIH-Frontend" cmd /k "cd /d c:\SIH\dashboard && npm start"

timeout /t 6 /nobreak

REM ========================================================================
REM   OPEN BROWSER
REM ========================================================================

echo [3/3] Opening Dashboard in Browser...
echo        URL: http://localhost:3000
echo.

start http://localhost:3000

REM ========================================================================
REM   READY MESSAGE
REM ========================================================================

echo.
echo ========================================================================
echo.
echo   SYSTEM ONLINE AND READY
echo.
echo   Backend:  http://localhost:8000 (API Docs)
echo   Frontend: http://localhost:3000 (Dashboard)
echo.
echo   Status:   RUNNING
echo.
echo   To stop: Close the Backend and Frontend windows
echo.
echo ========================================================================
echo.

pause
