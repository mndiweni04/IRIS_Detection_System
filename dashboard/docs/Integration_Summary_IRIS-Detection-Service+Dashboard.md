# Overview

This document outlines the current integration of the IRIS-Detection-Service backend with the PySimpleGUI-based dashboard. The goal is to simulate seamless real-time drowsiness detection updates without requiring the physical hardware (ESP32 glasses) yet.

## 1. Backend-Dashboard Communication

Backend Role:

Sends drowsiness state updates (Alert, Drowsy, metrics like blink_duration, avg_accel, nod_freq) to the dashboard.

Uses the existing controller.py logic to generate driver state predictions based on the ML model and baseline deviations.

Generates a state dictionary structured as:

state = {

    "connected": False,
    "duration": 0.0,
    "status": "Looking good",
    "metrics": {"avg_accel": 0.0, "blink_duration": 0.0, "nod_freq": 0.0}
}


Dashboard Role:

Receives state updates from the backend via a WebSocket client (ws_client.py) or simulated internal updates.

Updates the GUI elements:

Bluetooth status

Session ID and duration

Driver state button text and color

Circular progress bar

## 2. Dashboard Refactoring

Renaming for Clarity:

DashboardController → DashboardAppController (optional) to differentiate from backend Controller.

ButtonController → DriverStateController (manages state-dependent visuals).

DashboardView → DashboardGUI (represents UI layer).

Reorganized Directory Suggestion:

### IRIS_Dashboard/
    │
    ├─ dashboard/
    │   ├─ gui.py          # DashboardGUI
    │   ├─ controller.py   # DashboardAppController + DriverStateController
    │   ├─ components/     # Custom widgets (e.g., CircleProgress)
    │   └─ main.py
    └─ backend/             # IRIS-Detection-Service
        ├─ src/
        │   ├─ controller.py
        │   ├─ algorithm/
        │   ├─ bluetooth/
        │   ├─ data_cleansing/
        │   └─ feature_extraction/
        └─ ws_server.py

## 3. WebSocket Integration

Backend (ws_server.py):

Opens a WebSocket server to broadcast the state dictionary to connected clients.

Broadcast occurs whenever a new feature vector is processed.

Dashboard (ws_client.py):

Connects to the backend WebSocket server.

On message reception, updates GUI elements accordingly.

Outcome:

Dashboard now reflects simulated real-time drowsiness detection without requiring BLE hardware.

## 4. Remaining Work

Connect WebSocket integration to actual BLE input when hardware is available.

Add logging and error handling for network interruptions.

Implement the circular progress bar logic fully based on state["metrics"].

Optionally, refactor dashboard directory for cleaner structure and naming.

## 5. Commit Guidance

Use commit messages like:
"Integrated dashboard with backend via WebSocket; refactored GUI and controller naming"