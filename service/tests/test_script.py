import asyncio
import pandas as pd
import numpy as np
import pytest
from src.data_cleansing.data_processor import DataProcessor
from src.feature_extraction.feature_vector import FeatureExtractor
from src.algorithm.baseline import define_and_save_drowsiness_baseline, load_baseline
from src.algorithm.ml_models import load_models, predict_state
from src.config import FRAME_SIZE, SAMPLE_RATE, BLINK_THRESHOLD, NOD_THRESHOLD

# Mark async tests individually to avoid marking sync tests as asyncio coroutines
# ------------------------
# Test DataProcessor
# ------------------------
@pytest.mark.asyncio
async def test_data_processor():
    print("Testing DataProcessor...")
    queue = asyncio.Queue()
    processor = DataProcessor(queue)

    # ✅ FIX: Send JSON dicts directly (matches actual BLE usage)
    processor.process_data({"photodiode_value": 1000, "ay": 0.05, "gz": 0.0})
    processor.process_data({"photodiode_value": 980, "ay": 0.1, "gz": 0.0})

    assert len(processor.buffer) == 2, f"Buffer should contain 2 rows, got {len(processor.buffer)}"

    # Fill buffer to FRAME_SIZE
    for _ in range(FRAME_SIZE - 2):
        processor.process_data({"photodiode_value": 1000, "ay": 0.05, "gz": 0.0})

    frame = await queue.get()
    assert isinstance(frame, pd.DataFrame), "Queued frame should be DataFrame"
    assert len(frame) == FRAME_SIZE, f"Frame should have {FRAME_SIZE} rows, got {len(frame)}"
    assert len(processor.buffer) == 0, f"Buffer should be empty after queuing, got {len(processor.buffer)}"
    print("DataProcessor test passed.")

# ------------------------
# Test FeatureExtractor
# ------------------------
def test_feature_extractor():
    print("Testing FeatureExtractor...")
    extractor = FeatureExtractor(sample_rate=SAMPLE_RATE, blink_threshold=BLINK_THRESHOLD, nod_threshold=NOD_THRESHOLD)

    mock_data = pd.DataFrame({
        'photodiode_value': np.random.randint(900, 1100, FRAME_SIZE),
        'ay': np.random.rand(FRAME_SIZE) * 0.5,
        'gz': np.zeros(FRAME_SIZE)
    })

    # Simulate blinks
    mock_data.loc[100:110, 'photodiode_value'] = 100
    mock_data.loc[500:515, 'photodiode_value'] = 50
    # Simulate nodding
    mock_data.loc[250:265, 'gz'] = np.sin(np.linspace(0, np.pi*3, 16)) * 0.6

    blink_duration = extractor.getBlinkScalar(mock_data)
    nod_freq = extractor.getNodFreqScalar(mock_data)
    avg_accel = extractor.getAvgAccelScalar(mock_data)

    assert blink_duration > 0, "Blink duration should be positive"
    assert nod_freq >= 0, "Nod frequency non-negative"
    assert -1 <= avg_accel <= 1, "Average acceleration in expected range"
    print(f"Blink Duration: {blink_duration:.2f} ms, Nod Frequency: {nod_freq:.2f} Hz, Avg Accel: {avg_accel:.2f}")
    print("FeatureExtractor test passed.")

# ------------------------
# Test baseline and HMM
# ------------------------
def test_baseline_hmm():
    print("Testing Baseline + HMM integration...")
    # Ensure baseline exists
    define_and_save_drowsiness_baseline()
    baseline = load_baseline()
    assert baseline is not None, "Baseline should load"

    # Load HMM models
    alert_model, drowsy_model = load_models()

    # Mock feature vectors
    alert_vector = [250.0, 0.0, 0.0]  # avg_blink_ms, nod_freq, avg_accel
    drowsy_vector = [800.0, 1.0, 0.3]

    state_alert = predict_state(alert_vector, alert_model, drowsy_model)
    state_drowsy = predict_state(drowsy_vector, alert_model, drowsy_model)

    assert state_alert in ["Alert", "Drowsy"], "Prediction should return valid state"
    assert state_drowsy in ["Alert", "Drowsy"], "Prediction should return valid state"

    print(f"Alert vector predicted as: {state_alert}")
    print(f"Drowsy vector predicted as: {state_drowsy}")
    print("Baseline + HMM test passed.")
# ------------------------
# Integration test: full pipeline
# ------------------------
@pytest.mark.asyncio
async def test_integration():
    print("Testing full pipeline integration...")
    queue = asyncio.Queue()
    processor = DataProcessor(queue)
    extractor = FeatureExtractor(sample_rate=SAMPLE_RATE, blink_threshold=BLINK_THRESHOLD, nod_threshold=NOD_THRESHOLD)

    # ✅ FIX: Simulate drowsy-like BLE input with dicts (matches production)
    for i in range(FRAME_SIZE):
        # Simulate blinks every 100 samples
        ir_value = 100 if (i % 100 < 15) else 950
        processor.process_data({
            "photodiode_value": ir_value,
            "ay": 0.1,
            "gz": 0.5 if (i % 50 < 10) else 0.0  # Simulate nods
        })

    frame = await queue.get()

    # Extract features
    blink_duration = extractor.getBlinkScalar(frame)
    nod_freq = extractor.getNodFreqScalar(frame)
    avg_accel = extractor.getAvgAccelScalar(frame)

    # Load baseline and HMM
    baseline = load_baseline()
    alert_model, drowsy_model = load_models()

    # Compare with baseline
    deviations = {}
    if blink_duration > baseline["avg_blink_duration_ms"]:
        deviations["blink"] = blink_duration
    if nod_freq > baseline["nod_freq_hz"]:
        deviations["nod"] = nod_freq
    if abs(avg_accel) > baseline["avg_accel_ay"]:
        deviations["accel"] = avg_accel

    # HMM prediction
    feature_vector = [blink_duration, nod_freq, avg_accel]
    state = predict_state(feature_vector, alert_model, drowsy_model)

    print(f"Extracted features: Blink {blink_duration:.2f} ms, Nod {nod_freq:.2f} Hz, Accel {avg_accel:.2f}")
    print(f"Deviations from baseline: {deviations}")
    print(f"HMM predicted state: {state}")
    
    # ✅ Add assertions to verify features were extracted
    assert blink_duration > 0, "Integration test should detect blinks"
    assert nod_freq > 0, "Integration test should detect nods"
    
    print("Integration test passed.")

# ------------------------
# Run all tests
# ------------------------
async def main():
    await test_data_processor()
    test_feature_extractor()
    test_baseline_hmm()
    await test_integration()
    print("All tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
