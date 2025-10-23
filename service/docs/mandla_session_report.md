Session Completion Report

Project: IRIS-Detection-Service
Session Date: 2025-10-09
Goal: Fix HMM broadcast error, integrate feature extraction and algorithm, validate end-to-end pipeline.

1. Completed Tasks

Fixed ValueError: operands could not be broadcast in ml_models.py by adjusting feature vector shape.

Successfully trained and saved HMM models (alert_hmm.pkl and drowsy_hmm.pkl).

Implemented predict_state() for single-frame alert/drowsy classification.

Verified HMM model scoring with synthetic alert/drowsy vectors.

Updated test scripts:

Full unit tests for DataProcessor and FeatureExtractor.

Mocked BLEHandler callback integration with DataProcessor.

End-to-end integration test simulating pipeline flow.

Confirmed all tests pass with proper feature extraction and HMM prediction:

DataProcessor ✅

FeatureExtractor ✅

Baseline + HMM ✅

Full pipeline ✅

2. Issues Resolved

Broadcast mismatch error in HMM scoring due to wrong input array shape.

Path and module import issues for config.py and src packages.

Integration test failures due to missing HMM training were fixed by training models first.

3. Outstanding Tasks / Next Steps

Implement bidirectional BLE TX to ESP32.

Add error handling, logging, and monitoring in BLEHandler and Controller.

Integrate real BLE data flow (not just mocked).

Enhance data cleansing with normalization, missing value handling, and error recovery.

Implement input validation and exception handling in FeatureExtractor.

Extend HMM training and validation with real-world data.

Create a centralized configuration file (config/) for thresholds and sample rates.

4. Deliverables

Updated ml_models.py with working train_and_save_hmms() and predict_state()

Fully passing tests/test_script.py with end-to-end pipeline simulation

Verified HMM predictions for alert and drowsy synthetic vectors

Integration-ready pipeline verified in local environment

Running the Services

The IRIS-Detection-Service backend is modular, and each service can be run independently or together via the controller. Below are the instructions for running the key components:

1. Controller (Main Orchestration)

The controller orchestrates the BLE, data cleansing, feature extraction, and drowsiness detection pipeline.

# From the project root (service folder)
python -m src.controller.controller

2. Data Cleansing / Processor Tests

Run unit tests for the data processor:

# From the project root
python -m tests.test_script

3. Feature Extraction Tests

You can run feature extraction unit tests:

# From the project root
python -m tests.feature_extraction.test_feature_extractor

4. ML Models (HMM Training & Testing)

Train or reload HMM models:

# Train and save HMM models
python src/algorithm/ml_models.py


Use predict_state() from ml_models.py to test single-frame predictions programmatically.

Notes

Ensure that the Python environment has all required packages installed:

pip install -r requirements.txt


All relative paths in the project assume execution from the service folder.

For BLE communication, the target device must be powered on and within range.

Conclusion:
This session successfully fixed the HMM scoring issue, integrated baseline + ML algorithm into the pipeline, and validated end-to-end functionality with unit and integration tests. The system is now ready for real BLE data integration and further refinement of normalization, logging, and exception handling.