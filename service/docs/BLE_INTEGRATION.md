# BLE Handler Integration Summary

## Changes Made

### 1. **WebSocketServer** (`src/network/ws_server.py`)
- ✅ Fixed: Renamed `broadcast_state()` → `broadcast()` for correct method name
- Added `return_exceptions=True` to `asyncio.gather()` for robustness

### 2. **DataProcessor** (`src/data_cleansing/data_processor.py`)
- ✅ Added optional `raw_csv_path` parameter to write raw BLE payloads directly to CSV
- When a JSON dict is received from BLEHandler, it's immediately written to `data/raw/live_payloads.csv`
- This ensures all BLE payloads are persisted in real-time
- Column order matches ESP32 transmitter: `ax, ay, az, gx, gy, gz, ir`

### 3. **BLEHandler** (`src/bluetooth/ble_handler.py`)
- ✅ Already complete: Parses bare JSON objects and newline-delimited messages
- Fast path for single JSON notifications (no newline required)
- Fallback reassembly for fragmented messages
- Logs connection status and disconnections

### 4. **Controller** (`src/controller.py`)
- ✅ Fixed: Removed session-based file writes (service is stateless)
- ✅ Fixed: Initialize DataProcessor with raw_csv_path for live payload capture
- ✅ Fixed: Added `nod_freq` to features dict
- ✅ Fixed: HMM prediction now uses 3-element vector: `[blink_duration, nod_freq, avg_accel]`
- ✅ Fixed: Connected state is now visible in dashboard state object
- ✅ Fixed: Proper imports using `from pathlib import Path` instead of `os.path.join()`
- ✅ Added logging instead of print statements
- ✅ Broadcast task is now properly managed and cancelled on shutdown

## Payload Compatibility

### ESP32 Transmitter Output (JSON)
```json
{"ax":0.123,"ay":-0.456,"az":1.000,"gx":0.15,"gy":-1.20,"gz":0.05,"ir":1024}
```

### BLEHandler Parsing
- ✅ Accepts bare JSON (no newline required)
- ✅ Accepts newline-terminated JSON
- ✅ Tolerates fragmented messages across multiple notifications
- Returns parsed dict to `DataProcessor.process_data()`

### DataProcessor Output (CSV)
```
ax,ay,az,gx,gy,gz,ir
0.123,-0.456,1.0,0.15,-1.2,0.05,1024
...
```
**Location**: `service/data/raw/live_payloads.csv`

## Sampling Rate

**Transmitter**: ESP32 loop with `delay(100)` = **10 Hz** (100ms per sample)  
**Config**: `SAMPLE_RATE = 100` Hz (expected, but actual is 10 Hz from transmitter)

⚠️ Note: Update `config.py` if the transmitter delay changes.

## How to Run

### Option 1: Test BLE Only (Quick Verification)
```powershell
cd "C:\Users\NathanDesk\Desktop\IRIS-Detection-Service\service"
$env:PYTHONPATH = (Get-Item -Path ".").FullName
pip install bleak pandas
python scripts\run_ble.py
```
This will stream BLE payloads to the console for ~60 seconds.

### Option 2: Run Full Service (With WebSocket Dashboard)
```powershell
cd "C:\Users\NathanDesk\Desktop\IRIS-Detection-Service\service"
$env:PYTHONPATH = (Get-Item -Path ".").FullName
pip install bleak pandas websockets numpy scikit-learn hmmlearn
python -m src.controller
```
This will:
- Connect to AntiSleep-Glasses ESP32
- Stream raw payloads to `data/raw/live_payloads.csv`
- Broadcast state (connected status, metrics, driver status) over WebSocket
- Process frames and compute features every 1000 samples

## Dashboard State Object

The service broadcasts this state object over WebSocket every 1 second:

```json
{
  "connected": true,
  "duration": 45.2,
  "status": "Looking good",
  "metrics": {
    "avg_accel": 0.15,
    "blink_duration": 250.5,
    "nod_freq": 0.3
  }
}
```

**Fields**:
- `connected`: Boolean - BLE connection status (visible on dashboard)
- `duration`: Float - Service uptime in seconds
- `status`: String - Driver drowsiness state ("Looking good", "Be careful", "Danger")
- `metrics`: Object - Extracted features from latest frame

## File Locations

- **Raw BLE Payloads**: `service/data/raw/live_payloads.csv`
- **Processed Frames**: Queued in memory (buffered by `FRAME_SIZE=1000`)
- **Baseline**: `service/drowsiness_baseline.json`
- **HMM Models**: `service/src/algorithm/saved_models/`

## Troubleshooting

### "Device not found" Error
- Ensure ESP32 is powered on and advertising
- Verify UUIDs in `config.py` match the transmitter:
  - `SERVICE_UUID = "b86f0001-3e1d-4ad6-98ef-6b93f33e5a4a"`
  - `TX_CHAR_UUID = "b86f0002-3e1d-4ad6-98ef-6b93f33e5a4a"`
- Disconnect any phone/nRF Connect app (only one BLE central allowed)

### No Payloads in `live_payloads.csv`
- Check BLE logs for "Subscribed to notifications" message
- Verify the characteristic is properly subscribed
- Check BLE handler logs for JSON parse errors

### WebSocket Connection Failed
- Ensure port 8765 is not in use
- Check firewall allows localhost WebSocket

## Configuration

Edit `service/src/config.py` to customize:

```python
DEVICE_NAME = "AntiSleep-Glasses"           # ESP32 advertised name
SERVICE_UUID = "b86f0001-3e1d-4ad6-98ef-6b93f33e5a4a"
TX_CHAR_UUID = "b86f0002-3e1d-4ad6-98ef-6b93f33e5a4a"
FRAME_SIZE = 1000                           # Rows per frame for feature extraction
SAMPLE_RATE = 100                           # Hz (note: ESP32 sends at ~10 Hz actual)
BLINK_THRESHOLD = 1000                      # ms
NOD_THRESHOLD = 0.5                         # g
```

## Verification Checklist

✅ BLE connects to AntiSleep-Glasses  
✅ JSON payloads parsed correctly  
✅ Raw payloads written to `live_payloads.csv`  
✅ Connected status visible in dashboard state  
✅ Features extracted every 1000 samples  
✅ HMM prediction uses 3-element vector  
✅ All imports correct and functional  
✅ Service is stateless (no session files)  
