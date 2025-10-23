# 🔍 IRIS-Detection-Service - Comprehensive Diagnostic & Fix Plan

**Generated**: October 21, 2025  
**Status**: 🔴 Critical Issues Identified  

---

## 🚨 CRITICAL ISSUES IDENTIFIED

### 1. ❌ **IMPORT ERRORS - Relative Imports Without Package Context**

**Root Cause**: `controller.py` and all modules use **relative imports** but are NOT being run as a module.

**Current Problematic Imports** (in `service/src/controller.py`):
```python
from data_cleansing.data_processor import DataProcessor  # ❌ FAILS
from bluetooth.ble_handler import BLEHandler              # ❌ FAILS
from feature_extraction.feature_vector import FeatureExtractor  # ❌ FAILS
from algorithm.baseline import load_baseline              # ❌ FAILS
from algorithm.ml_models import load_models               # ❌ FAILS
from config import SAMPLE_RATE                            # ❌ FAILS
from network.ws_server import WebSocketServer             # ❌ FAILS
```

**Why It Fails**:
- When running `python -m src.controller`, Python looks for `data_cleansing`, `bluetooth`, etc. in:
  1. Current directory
  2. Python path
  3. **BUT NOT in the `src/` directory**
  
- The imports should be either:
  - **Absolute**: `from src.data_cleansing.data_processor import ...`
  - **Relative with dot**: `from .data_cleansing.data_processor import ...`

**Evidence from Errors**:
```
service/__main__.py:13: Import "controller" could not be resolved
```

---

### 2. ❌ **BLUETOOTH DEVICE NAME MISMATCH**

**Config Says**: `DEVICE_NAME = "AntiSleep-Glasses"`  
**Arduino Says**: `BLE_NAME = "AntiSleep-Glasses-ESP32"`  

**Files Affected**:
- `service/src/config.py` (line 2)
- `service/transmitter_doc.ino` (line 23)

**Impact**: BLE scanner will NEVER find the device because the names don't match.

---

### 3. ❌ **CIRCULAR/INCORRECT IMPORT IN bluetooth/__init__.py**

**Current Code** (`service/src/bluetooth/__init__.py`):
```python
from .ble_handler import BLEHandler
from config import DEVICE_NAME, TX_CHAR_UUID  # ❌ Should be "from ..config"
```

**Problem**: Imports `config` without relative path, won't work in package context.

---

### 4. ⚠️ **BASELINE FILE NOT CREATED**

**Error**: `RuntimeError: Baseline not found. Please create it before starting.`

**Root Cause**: 
- `controller.py` line 35 raises error if baseline doesn't exist
- Baseline file should be at `service/src/drowsiness_baseline.json`
- File exists but may not be in correct location

---

### 5. ⚠️ **TEST SCRIPT HAS POTENTIAL NONE ERRORS**

**Errors** (`service/tests/test_script.py` lines 116, 118, 120):
```python
if blink_duration > baseline["avg_blink_duration_ms"]:  # baseline could be None
```

**Impact**: If `load_baseline()` returns None, test will crash.

---

## 🛠️ COMPREHENSIVE FIX PLAN

### **Phase 1: Fix Import Structure (CRITICAL - 30 minutes)**

#### Fix 1.1: Update ALL imports in controller.py to be relative

**File**: `service/src/controller.py`

**Change FROM**:
```python
from data_cleansing.data_processor import DataProcessor
from bluetooth.ble_handler import BLEHandler
from feature_extraction.feature_vector import FeatureExtractor
from algorithm.baseline import load_baseline, define_and_save_drowsiness_baseline
from algorithm.ml_models import load_models, predict_state
from config import SAMPLE_RATE, BLINK_THRESHOLD, NOD_THRESHOLD
from network.ws_server import WebSocketServer
```

**Change TO**:
```python
from .data_cleansing.data_processor import DataProcessor
from .bluetooth.ble_handler import BLEHandler
from .feature_extraction.feature_vector import FeatureExtractor
from .algorithm.baseline import load_baseline, define_and_save_drowsiness_baseline
from .algorithm.ml_models import load_models, predict_state
from .config import SAMPLE_RATE, BLINK_THRESHOLD, NOD_THRESHOLD
from .network.ws_server import WebSocketServer
```

---

#### Fix 1.2: Update bluetooth/__init__.py

**File**: `service/src/bluetooth/__init__.py`

**Change FROM**:
```python
from .ble_handler import BLEHandler
from config import DEVICE_NAME, TX_CHAR_UUID
```

**Change TO**:
```python
from .ble_handler import BLEHandler
from ..config import DEVICE_NAME, TX_CHAR_UUID
```

---

#### Fix 1.3: Update ble_handler.py imports

**File**: `service/src/bluetooth/ble_handler.py` (line 6)

**Change FROM**:
```python
from config import DEVICE_NAME, TX_CHAR_UUID, SERVICE_UUID
```

**Change TO**:
```python
from ..config import DEVICE_NAME, TX_CHAR_UUID, SERVICE_UUID
```

---

#### Fix 1.4: Update data_processor.py imports

**File**: `service/src/data_cleansing/data_processor.py`

**Change FROM**:
```python
from config import FRAME_SIZE
```

**Change TO**:
```python
from ..config import FRAME_SIZE
```

---

#### Fix 1.5: Update __main__.py to run correctly

**File**: `service/__main__.py`

**Current Code**:
```python
# Add service/src to path so imports work
service_dir = Path(__file__).parent
sys.path.insert(0, str(service_dir / "src"))

# Now import and run the controller
from controller import main
```

**Change TO**:
```python
# Run as module without path manipulation
from src.controller import main
```

---

### **Phase 2: Fix Bluetooth Device Name (CRITICAL - 5 minutes)**

#### Fix 2.1: Update config.py to match Arduino

**File**: `service/src/config.py` (line 2)

**Change FROM**:
```python
DEVICE_NAME = "AntiSleep-Glasses"
```

**Change TO**:
```python
DEVICE_NAME = "AntiSleep-Glasses-ESP32"  # Must match Arduino BLE_NAME exactly
```

**OR** update Arduino to remove "-ESP32" suffix if you prefer shorter name.

---

### **Phase 3: Fix Baseline Creation (HIGH PRIORITY - 10 minutes)**

#### Fix 3.1: Create baseline before running service

**Run this command ONCE**:
```powershell
cd c:\Users\NathanDesk\Desktop\IRIS-Detection-Service\service
python -c "import sys; sys.path.insert(0, 'src'); from algorithm.baseline import define_and_save_drowsiness_baseline; define_and_save_drowsiness_baseline('src/drowsiness_baseline.json')"
```

**This creates**: `service/src/drowsiness_baseline.json`

#### Fix 3.2: Update baseline.py to use correct path

**File**: `service/src/algorithm/baseline.py`

**Change FROM**:
```python
BASELINE_PATH = "drowsiness_baseline.json"
```

**Change TO**:
```python
import os
BASELINE_PATH = os.path.join(os.path.dirname(__file__), "..", "drowsiness_baseline.json")
```

---

### **Phase 4: Fix Test Script (MEDIUM PRIORITY - 10 minutes)**

#### Fix 4.1: Add None check in test_integration

**File**: `service/tests/test_script.py` (lines 114-121)

**Change FROM**:
```python
# Compare with baseline (simple deviation check)
deviations = {}
if blink_duration > baseline["avg_blink_duration_ms"]:
    deviations["blink"] = blink_duration
if nod_freq > baseline["nod_freq_hz"]:
    deviations["nod"] = nod_freq
if abs(avg_accel) > baseline["avg_accel_ay"]:
    deviations["accel"] = avg_accel
```

**Change TO**:
```python
# Compare with baseline (simple deviation check)
deviations = {}
if baseline:  # Check baseline exists
    if blink_duration > baseline.get("avg_blink_duration_ms", 0):
        deviations["blink"] = blink_duration
    if nod_freq > baseline.get("nod_freq_hz", 0):
        deviations["nod"] = nod_freq
    if abs(avg_accel) > baseline.get("avg_accel_ay", 0):
        deviations["accel"] = avg_accel
else:
    print("Warning: Baseline not available for comparison")
```

---

## 🧪 VERIFICATION STEPS

### Step 1: Fix All Imports
```powershell
# Apply all fixes from Phase 1
# Then verify imports work:
cd c:\Users\NathanDesk\Desktop\IRIS-Detection-Service\service
python -c "from src.controller import main; print('✅ Imports work!')"
```

**Expected**: ✅ Imports work!  
**If Error**: Re-check all relative import changes (`.` prefix added)

---

### Step 2: Create Baseline
```powershell
cd c:\Users\NathanDesk\Desktop\IRIS-Detection-Service\service
python -m src.algorithm.baseline
```

**Expected**: `Drowsiness detection baseline saved to src/drowsiness_baseline.json`

---

### Step 3: Test BLE Device Discovery
```powershell
# Turn ON your ESP32 first!
cd c:\Users\NathanDesk\Desktop\IRIS-Detection-Service\service
python -m src.bluetooth.ble_handler
```

**Expected**: Should scan and find "AntiSleep-Glasses-ESP32"  
**If Not Found**: 
- Verify ESP32 is powered on
- Check device name in Windows Bluetooth settings
- Update `DEVICE_NAME` in config.py to match EXACTLY

---

### Step 4: Run Full Service
```powershell
cd c:\Users\NathanDesk\Desktop\IRIS-Detection-Service\service
python -m src.controller
```

**Expected Output**:
```
INFO:root:Controller started.
INFO:root:Scanning for BLE device 'AntiSleep-Glasses-ESP32'...
INFO:root:Found device AntiSleep-Glasses-ESP32 @ XX:XX:XX:XX:XX:XX. Connecting...
INFO:root:Connected to peripheral.
INFO:root:Subscribed to notifications...
INFO:websockets.server:server listening on localhost:8765
```

---

## 📊 SUMMARY OF ALL FIXES NEEDED

| # | Issue | Severity | File | Fix |
|---|-------|----------|------|-----|
| 1 | Relative imports missing `.` | 🔴 CRITICAL | `src/controller.py` | Add `.` prefix to all imports |
| 2 | bluetooth/__init__ wrong import | 🔴 CRITICAL | `src/bluetooth/__init__.py` | Change `from config` to `from ..config` |
| 3 | ble_handler wrong import | 🔴 CRITICAL | `src/bluetooth/ble_handler.py` | Change `from config` to `from ..config` |
| 4 | data_processor wrong import | 🔴 CRITICAL | `src/data_cleansing/data_processor.py` | Change `from config` to `from ..config` |
| 5 | __main__.py path manipulation | 🔴 CRITICAL | `service/__main__.py` | Use `from src.controller import main` |
| 6 | BLE device name mismatch | 🔴 CRITICAL | `src/config.py` | Change to "AntiSleep-Glasses-ESP32" |
| 7 | Baseline file missing | 🟡 HIGH | Run command | Create baseline JSON |
| 8 | Baseline path hardcoded | 🟡 HIGH | `src/algorithm/baseline.py` | Use `os.path.join()` for relative path |
| 9 | Test None checks | 🟢 MEDIUM | `tests/test_script.py` | Add `if baseline:` check |

---

## 🚀 QUICK FIX SEQUENCE (Copy-Paste Ready)

### 1. Fix Bluetooth Device Name (30 seconds)
Edit `service/src/config.py` line 2:
```python
DEVICE_NAME = "AntiSleep-Glasses-ESP32"
```

### 2. Create Baseline (30 seconds)
```powershell
cd c:\Users\NathanDesk\Desktop\IRIS-Detection-Service\service
python -m src.algorithm.baseline
```

### 3. Apply all import fixes manually (use find-replace):
- In `src/controller.py`: Replace `from data_cleansing` with `from .data_cleansing` (etc.)
- In `src/bluetooth/__init__.py`: Replace `from config` with `from ..config`
- In `src/bluetooth/ble_handler.py`: Replace `from config` with `from ..config`
- In `src/data_cleansing/data_processor.py`: Replace `from config` with `from ..config`
- In `service/__main__.py`: Replace `from controller` with `from src.controller`

### 4. Test
```powershell
cd c:\Users\NathanDesk\Desktop\IRIS-Detection-Service\service
python -m src.controller
```

---

## ⚠️ BLUETOOTH TROUBLESHOOTING

If BLE still can't find device after name fix:

### Check 1: Verify ESP32 is advertising
```powershell
# In Windows, open Settings > Bluetooth & devices
# Look for "AntiSleep-Glasses-ESP32" in available devices
```

### Check 2: Check exact BLE name being advertised
Upload this test sketch to ESP32:
```cpp
void setup() {
    Serial.begin(115200);
    NimBLEDevice::init("AntiSleep-Glasses-ESP32");  // EXACT name
    Serial.println("BLE Name: AntiSleep-Glasses-ESP32");
}
```

### Check 3: Try fallback name scan
Temporarily modify `ble_handler.py` to print all discovered devices:
```python
devices = await BleakScanner.discover()
for d in devices:
    print(f"Found: {d.name} @ {d.address}")
```

---

**Status**: Ready to apply fixes  
**Estimated Fix Time**: 1 hour total  
**Priority**: Apply Phase 1 & 2 first (import + BLE name)
