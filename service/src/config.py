DEVICE_NAME = "AntiSleep-Glasses-ESP32" 
SERVICE_UUID = "b86f0001-3e1d-4ad6-98ef-6b93f33e5a4a"
TX_CHAR_UUID = "b86f0002-3e1d-4ad6-98ef-6b93f33e5a4a"
BLINK_THRESHOLD = 250 
NOD_THRESHOLD = 0.5
FRAME_SIZE = 50   # CRITICAL FIX: Reduced from 1000 to 50 rows (5-second analysis frame)
SAMPLE_RATE = 10  # Hz, ACTUAL sampling rate from device (10 Hz)

# -----------Feature Extraction Parameters ----------- #