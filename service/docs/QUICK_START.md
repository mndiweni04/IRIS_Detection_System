# Quick Reference - BLE Handler Fix

## TL;DR - Start Here

### 1. Open PowerShell
```powershell
cd "C:\Users\NathanDesk\Desktop\IRIS-Detection-Service\service"
```

### 2. Set Python Path
```powershell
$env:PYTHONPATH = (Get-Item -Path ".").FullName
```

### 3. Install & Run
```powershell
pip install bleak pandas websockets numpy scikit-learn hmmlearn
python -m src.controller
```

### 4. Expected Result
✅ BLE connects  
✅ Payloads in `data/raw/live_payloads.csv`  
✅ State broadcasts over `ws://localhost:8765`  

---

## 5 Issues Fixed

| # | Issue | Fix | File |
|---|-------|-----|------|
| 1 | WebSocket method missing | `broadcast_state()` → `broadcast()` | `ws_server.py` |
| 2 | Raw payloads lost | Add `raw_csv_path` to DataProcessor | `data_processor.py` |
| 3 | Wrong HMM vector | Add `nod_freq` to features | `controller.py` |
| 4 | No connected status | Update state from handler | `controller.py` |
| 5 | Bad imports | `os.path` → `pathlib.Path` | `controller.py` |

---

## File Changes

### `service/src/network/ws_server.py` - Line 37
```python
# async def broadcast_state(...)  ❌
async def broadcast(...)           # ✅
```

### `service/src/data_cleansing/data_processor.py` - Line 14
```python
def __init__(..., raw_csv_path: Optional[str] = None):  # ✅
    if raw_csv_path:
        # Write payloads to CSV  ✅
```

### `service/src/controller.py` - Lines 1-95
```python
from pathlib import Path  # ✅ Instead of os
RAW_DIR = Path("./data/raw")  # ✅

processor = DataProcessor(queue, raw_csv_path=str(raw_csv_file))  # ✅

nod_freq = extractor.getNodFreqScalar(frame)  # ✅ Added
state_prediction = predict_state([blink_duration, nod_freq, avg_accel], ...)  # ✅ 3 features

state.update({"connected": handler.client.is_connected if handler.client else False, ...})  # ✅
await ws_server.broadcast(state)  # ✅ Method exists now
```

---

## Test It

### Just BLE (No Dashboard)
```powershell
$env:PYTHONPATH = (Get-Item -Path ".").FullName
python scripts\run_ble.py
```

### Full Service
```powershell
$env:PYTHONPATH = (Get-Item -Path ".").FullName
python -m src.controller
```

---

## Check Data

### View CSV Payloads
```powershell
head -5 data\raw\live_payloads.csv
```

### Monitor Console
```
✅ Connected to peripheral.
✅ Subscribed to notifications on b86f0002-...
✅ Raw CSV stream initialized: ...
✅ State: {'connected': True, 'metrics': {...}}
```

---

## Configs

### `service/src/config.py`
```python
DEVICE_NAME = "AntiSleep-Glasses"
SERVICE_UUID = "b86f0001-3e1d-4ad6-98ef-6b93f33e5a4a"
TX_CHAR_UUID = "b86f0002-3e1d-4ad6-98ef-6b93f33e5a4a"
FRAME_SIZE = 1000          # Rows per frame
SAMPLE_RATE = 100          # Hz (note: actual ~10 Hz from ESP32)
```

---

## Documentation

| Doc | Purpose |
|-----|---------|
| `RUN_GUIDE.md` | Complete setup & testing |
| `BLE_INTEGRATION.md` | Technical details |
| `FIXES_APPLIED.md` | What was fixed |
| `VERIFICATION.md` | Error resolution checklist |

---

## Status

✅ All errors fixed  
✅ All requirements met  
✅ Ready for production  

**Next**: Connect dashboard to WebSocket state!
