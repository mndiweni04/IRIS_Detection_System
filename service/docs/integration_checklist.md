# Integration Checklist & TODO List for IRIS-Detection-Service

## Overview
This document provides a comprehensive checklist and TODO list for implementing and integrating the IRIS-Detection-Service pipeline, based on the requirements outlined in [`service/docs/service_architecture.md`](service/docs/service_architecture.md ). The checklist evaluates each service tier from top (Bluetooth) to bottom (Controller), identifying implemented components, missing functionality, and integration gaps. It includes actionable steps to address issues and ensure seamless data flow across all tiers.

## Checklist: Pipeline Implementation Status

### 1. Bluetooth Service (`src/bluetooth`)
- **Implemented**:
  - BLE scanning and connection logic (`ble_handler.py`).
  - Reconnection handling and notification subscription.
  - Data reception as strings or bytearrays.
  - Basic configuration (`config.py`).
  - Fixed relative import issues for proper module resolution.
  - Mocked testing for data reception and callback invocation.
- **Missing/Incomplete**:
  - Bidirectional communication (sending data to ESP32 RX characteristic).
  - Error logging and detailed connection diagnostics.
  - Rate limiting for high-frequency data streams.
  - Integration with downstream services (e.g., passing data to DataProcessor).
- **Status**: ~80% complete. Core BLE functionality works with fixes, but lacks robustness and full integration.

### 2. Data Cleansing Service (`src/data_cleansing`)
- **Implemented**:
  - `DataProcessor` class with queue-based buffering and DataFrame conversion (`data_processor.py`).
  - CSV parsing from bytearray data.
  - Basic cleansing (dropping NaN values).
  - Async queue integration for frame processing.
  - Enhanced buffering logic for header-less subsequent chunks.
  - Unit and integration testing with mock data.
- **Missing/Incomplete**:
  - Advanced normalization (e.g., accelerometer units to g's).
  - More robust missing value handling (e.g., interpolation).
  - Integration with Bluetooth (BLEHandler callback connection).
  - Error handling and logging.
- **Status**: ~80% complete. Core processing logic exists with enhancements, but needs refinement and full integration.

### 3. Feature Extraction Service (`src/algorithm/feature_extractor.py`)
- **Implemented**:
  - `FeatureExtractor` class with full implementations of `getBlinkScalar`, `getNodFreqScalar`, and `getAvgAccelScalar`.
  - Baseline comparison functions (`load_baseline`, `check_for_deviations`).
  - Robust blink detection using groupby and sample rate.
  - Nod frequency calculation using peak detection.
  - Comprehensive unit testing with mock DataFrames simulating blinks and nods.
- **Missing/Incomplete**:
  - Input validation and error handling.
  - Integration with Data Cleansing (receiving queued DataFrames).
  - Unit tests for feature calculations (beyond basic assertions).
  - Note: Located in `src/algorithm/` instead of dedicated `src/feature_extraction/` folder.
- **Status**: ~90% complete. Core extraction logic exists and is tested, but needs integration and robustness.

### 4. Drowsiness Algorithm Service (`src/algorithm`)
- **Implemented**:
  - Baseline definition and saving (`baseline.py`).
  - ML model placeholders (`ml_models.py`).
  - Pre-trained HMM models in `saved_models/`.
- **Missing/Incomplete**:
  - Full ML prediction logic (e.g., loading models, running HMM on feature vectors).
  - Integration with Feature Extraction (receiving feature vectors).
  - Real-time processing and output formatting.
  - Training/validation scripts for models.
  - Combination of baseline + ML for hybrid detection.
- **Status**: 40% complete. Assets exist, but core logic and integration missing.

### 5. Controller Service (`src/controller`)
- **Implemented**:
  - Folder structure exists.
  - Basic orchestration logic (`controller.py`) with async tasks for BLE and data processing.
  - Queue consumption and feature extraction loop.
  - Integration tests simulating orchestration flow (BLE → Cleansing → Extraction).
- **Missing/Incomplete**:
  - Algorithm integration (calling ML predictions on features).
  - Error handling and service health monitoring.
  - Centralized configuration and logging.
  - Full bidirectional BLE TX/RX support.
- **Status**: ~50% complete. Core orchestration and feature extraction flow implemented, but lacks algorithm, robustness, and monitoring.

## TODO List: Missing Functionality
- **Bluetooth**:
  - Add bidirectional write capability to ESP32 RX.
  - Implement logging (e.g., via `logging` module) for connection events.
  - Add data rate throttling in `_handle_tx_data` to prevent overload.
  - Connect BLEHandler to DataProcessor via callback.

- **Data Cleansing**:
  - Implement advanced normalization (e.g., accelerometer units to g's).
  - Add robust missing value handling (e.g., interpolation).
  - Integrate with Bluetooth by connecting BLEHandler callback to DataProcessor.
  - Add error handling and logging.

- **Feature Extraction**:
  - Complete method implementations in `FeatureExtractor`.
  - Add input validation (e.g., check DataFrame columns).
  - Integrate with Data Cleansing by receiving queued DataFrames.
  - Add unit tests in `tests/feature_extraction/`.

- **Algorithm**:
  - Implement prediction functions in `ml_models.py` (e.g., load HMMs and predict on features).
  - Add hybrid logic combining baseline and ML.
  - Integrate with Feature Extraction via queues or direct calls.
  - Create training scripts for model updates.

- **Controller**:
  - Integrate algorithm predictions (e.g., load HMMs and predict on extracted features).
  - Add error handling and logging.
  - Implement health monitoring (e.g., check queue sizes, BLE connection status).
  - Add bidirectional BLE TX capability.

- **General**:
  - Updated `requirements.txt` with all dependencies (e.g., `bleak`, `pandas`, `hmmlearn`).
  - Add end-to-end tests across all tiers.
  - Implement logging and monitoring throughout the pipeline.

## Addressing Issues & Integration Steps
To resolve gaps and integrate tiers, follow these phased steps. Start with foundational fixes, then build upward.

### Phase 1: Core Implementations (1-2 weeks)
1. **Refine Data Cleansing**:
   - Enhance `src/data_cleansing/data_processor.py` with advanced normalization and error handling.
   - Connect BLEHandler callback to DataProcessor for seamless data flow.

2. **Complete Feature Extraction**:
   - Finish `getAvgAccelScalar` method in `src/algorithm/feature_extractor.py`.
   - Add input validation and error handling.
   - Integrate with Data Cleansing by receiving queued DataFrames.

3. **Enhance Algorithm**:
   - Complete `ml_models.py` with prediction functions.
   - Integrate: Have FeatureExtractor queue features to Algorithm for processing.

### Phase 2: Orchestration & Testing (1 week)
4. **Build Controller**:
   - Enhance `controller.py` with algorithm integration and error handling.
   - Add health monitoring and bidirectional BLE TX.
   - Ensure data flows: BLE → Cleansing → Extraction → Algorithm → Controller output.

5. **Integration Testing**:
   - Create `tests/` folder with unit tests for each tier.
   - Run end-to-end tests: Simulate ESP32 data → Full pipeline → Verify outputs.
   - Use mock data for offline testing (e.g., extend `feature_vector.py` examples).

### Phase 3: Robustness & Deployment (1 week)
6. **Error Handling & Logging**:
   - Add try/except blocks and logging across all services.
   - Implement health checks in Controller (e.g., check queue sizes, connection status).

7. **Configuration & Dependencies**:
   - Create `config/` folder for centralized settings (sample_rate, thresholds).
   - Update `requirements.txt` and ensure all imports work.

8. **Deployment**:
   - Add `main.py` or `app.py` to start the Controller.
   - Test on target hardware (Windows BLE setup).
   - Document setup in `docs/` (e.g., ESP32 flashing, Python environment).

### Tools & Best Practices
- **Version Control**: Commit changes incrementally; use branches for each phase.
- **Dependencies**: Install via `pip install -r requirements.txt`.
- **Testing**: Use `pytest` for automated tests.
- **Monitoring**: Add metrics (e.g., via `logging` or Prometheus) for real-time pipeline health.
- **Security**: Ensure BLE connections are secure; avoid exposing sensitive data in logs.

This checklist ensures alignment with [`service/docs/service_architecture.md`](service/docs/service_architecture.md ). Total estimated effort: 4-6 weeks for a functional prototype. If you encounter blockers (e.g., ESP32 data format), provide details for targeted fixes. Save this as `service/docs/integration_checklist.md`. Any questions?