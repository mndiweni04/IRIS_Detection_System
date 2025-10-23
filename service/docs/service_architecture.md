# Backend Architecture: Drowsiness Detection System

## Overview
The backend architecture is a modular, pipeline-based system designed to process physiological data in real-time to detect user drowsiness. The system is composed of several independent services, each with a specific responsibility, which allows for a clean separation of concerns and future scalability. The data flows sequentially through the following stages: data collection, cleansing, feature extraction, and finally, the core detection algorithm.

## Service Pipeline

### 1. Bluetooth Service (`src/bluetooth`)
- **Function:** Initial entry point for all physiological data. Responsible for Bluetooth scanning, establishing a secure connection with a wearable device, and streaming raw sensor data packets.
- **Data Output:** Raw, time-series data streams (e.g., from accelerometers, gyroscopes, and other sensors) from the connected device.

### 2. Data Cleansing Service (`src/data_cleansing`)
- **Function:** Receives the raw data stream and prepares it for analysis. Performs essential data preprocessing steps.
- **Key Processes:**
  - Buffering/Queueing: Temporarily stores data packets to ensure a consistent and reliable data stream.
  - Conversion: Appends data to a structured format, such as a pandas DataFrame, for easier manipulation.
  - Normalization: Normalizes data to a common scale (e.g., dividing accelerometer readings by 9.81 to convert from raw units to g's).
  - Missing Value Handling: Implements strategies to fill or remove missing data points to prevent errors in subsequent stages.
- **Data Output:** A clean, normalized, and structured dataset ready for feature extraction.

### 3. Feature Extraction Service (`src/feature_extraction`)
- **Function:** Analyzes the cleaned data to extract meaningful, high-level features that are indicative of drowsiness. Converts raw sensor readings into quantifiable metrics.
- **Key Features Extracted:**
  - AVERAGE blink duration of a particular window (ms): Calculates the average duration of eye closures over a defined time period, measured in milliseconds.
  - AVERAGE acceleration about ay (nodding acceleration): Determines the average vertical acceleration of the user's head over a defined period to detect nodding behavior.
  - Nodding frequency (measured as gyroscope about the gz axis): Measures the rate of nodding over a set duration by analyzing the rotational data from the gyroscope's Z-axis.
- **Data Output:** A feature vector containing the calculated metrics.

### 4. Drowsiness Algorithm Service (`src/algorithm`)
- **Function:** Core logical component of the system. Receives the feature vector and applies a defined algorithm to determine the user's drowsiness level.
- **Core Logic (Pseudocode):**
  - Behavioral Logic: Employs a series of if-else or switch blocks to detect sleepy behaviors based on the combination of features from the previous stage. For example, a combination of long blink durations, high head movement, and low blink frequency could trigger a "drowsy" state.
  - Statistical Analysis:
    - Deviation from Ideal State: Uses statistical analysis to measure how far the current feature vector deviates from a predefined "alert" or "ideal" state.
    - Confidence Measurement: Performs correlation and convergence analysis on the time-series data to determine the variability and confidence of the drowsiness prediction.

### 5. Controller Service (`src/controller`)
- **Function:** Serves as the main application layer and RESTful API. Orchestrates the flow of data through the entire pipeline, from data collection to final output. Handles incoming requests from the frontend and returns the drowsiness detection results.
- **Key Responsibility:** Manages the communication between the services and exposes a clean, stable API to the client.
