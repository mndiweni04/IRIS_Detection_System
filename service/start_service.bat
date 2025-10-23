@echo off
REM Quick start script for IRIS-Detection-Service

setlocal enabledelayedexpansion

cd /d "C:\Users\NathanDesk\Desktop\IRIS-Detection-Service\service"

echo.
echo ========================================
echo IRIS-Detection-Service - BLE Test
echo ========================================
echo.

REM Set PYTHONPATH
set PYTHONPATH=%CD%

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+
    exit /b 1
)

REM Install dependencies
echo Installing required packages...
pip install bleak pandas websockets numpy scikit-learn hmmlearn -q

REM Run the service
echo.
echo Starting IRIS-Detection-Service...
echo Press Ctrl+C to stop
echo.
echo Expected output:
echo   - "[INFO] Scanning for BLE device 'AntiSleep-Glasses'..."
echo   - "[INFO] Connected to peripheral."
echo   - "[INFO] Subscribed to notifications..."
echo   - JSON payloads will be written to: data\raw\live_payloads.csv
echo   - State will be broadcast over WebSocket (ws://localhost:8765)
echo.

python -m src.controller

pause
