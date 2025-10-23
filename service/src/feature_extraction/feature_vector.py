import pandas as pd
import numpy as np
import itertools
import logging
from scipy.signal import find_peaks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureExtractor:
    """
    Extracts key features from a pandas DataFrame of time-series sensor data.
    
    Expected columns:
    - photodiode_value: IR photodiode reading in mV (0-3300 range)
    - ay: Accelerometer Y-axis in g
    - gz: Gyroscope Z-axis in °/s
    
    If 'ir' column exists (from raw BLE), it will be treated as photodiode_value.
    """
    def __init__(self, sample_rate=10, blink_threshold=250, nod_threshold=0.5):
        """
        Args:
            sample_rate: Sampling rate in Hz (ACTUAL rate from device, ~10 Hz for ESP32 with 100ms delay)
            blink_threshold: Threshold in mV for photodiode blink detection (normal ~300-500 mV, blink ~50-200 mV)
            nod_threshold: Threshold in g for gyroscope peak detection during nodding
        """
        self.sample_rate = sample_rate
        self.blink_threshold = blink_threshold
        self.nod_threshold = nod_threshold
        logger.info(f"FeatureExtractor initialized: sample_rate={sample_rate} Hz, blink_threshold={blink_threshold} mV, nod_threshold={nod_threshold} g")

    def getBlinkScalar(self, data: pd.DataFrame) -> float:
        """
        Calculates the average blink duration within a time window.
        Uses photodiode_value (IR reading in mV).
        
        Blink detection: photodiode_value < threshold (eye closes → IR drops)
        Returns the average duration in milliseconds.
        """
        if data.empty:
            return 0.0
        
        # Handle both 'photodiode_value' and 'ir' column names
        ir_column = None
        if 'photodiode_value' in data.columns:
            ir_column = 'photodiode_value'
        elif 'ir' in data.columns:
            ir_column = 'ir'
        else:
            logger.warning("Neither 'photodiode_value' nor 'ir' column found in data")
            return 0.0

        # Create a boolean series where True indicates the value is below the blink threshold
        # This captures both short blinks and sustained eye closures.
        is_blinking = data[ir_column] < self.blink_threshold
        blink_durations = []

        # Use groupby to find consecutive blocks of True values (blinks)
        for key, group in itertools.groupby(is_blinking):
            if key:
                # Calculate the duration of the single, continuous blink event
                duration_in_points = len(list(group))
                duration_ms = (duration_in_points / self.sample_rate) * 1000
                blink_durations.append(duration_ms)

        if not blink_durations:
            return 0.0
        
        avg_blink = float(np.mean(blink_durations))
        logger.debug(f"Blink extraction: found {len(blink_durations)} blinks, avg duration {avg_blink:.1f} ms")
        return avg_blink
        

    def getNodFreqScalar(self, data: pd.DataFrame) -> float:
        """
        Calculates the nodding frequency from gyroscope data (gz axis).
        Returns the frequency in Hz.
        """
        if data.empty or 'gz' not in data.columns:
            return 0.0
        
        # Use find_peaks to identify nodding events
        # The distance parameter is crucial to avoid detecting multiple peaks from a single nod
        peaks, _ = find_peaks(data['gz'].abs(), height=self.nod_threshold, distance=self.sample_rate / 10)
        
        if len(peaks) < 2:
            return 0.0

        time_of_first_peak = peaks[0] / self.sample_rate
        time_of_last_peak = peaks[-1] / self.sample_rate
        total_time = time_of_last_peak - time_of_first_peak

        if total_time == 0:
            return 0.0
        
        # Frequency is the number of peaks over the duration
        return (len(peaks) - 1) / total_time

    def getAvgAccelScalar(self, data: pd.DataFrame) -> float:
        """
        Calculates the average acceleration about the ay axis.
        Returns the average acceleration.
        """
        if data.empty or 'ay' not in data.columns:
            return 0.0
        
        return data['ay'].mean()

# Example usage with mock data
if __name__ == '__main__':

    # Set pandas options to display the full DataFrame
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    
    # Create a mock DataFrame representing a 10-second data window
    sample_rate = 100
    mock_data = pd.DataFrame({
        'photodiode_value': np.random.randint(900, 1100, 1000),
        'ay': np.random.rand(1000) * 0.5,
        'gz': np.zeros(1000)
    })

    # Simulate blinks (drops in photodiode value)
    # mock_data.loc[100:105, 'photodiode_value'] = np.random.randint(50, 150, 6)
    # mock_data.loc[500:510, 'photodiode_value'] = np.random.randint(50, 150, 11)

    # # Simulate a nodding movement (spikes in gz and ay values)
    # # The amplitude of 5 is well above the nod_threshold of 0.5
    # mock_data.loc[250:270, 'gz'] = np.sin(np.linspace(0, np.pi * 5, 21)) * 5
    # mock_data.loc[250:270, 'ay'] = np.sin(np.linspace(0, np.pi * 5, 21)) * 0.8
    
    # extractor = FeatureExtractor(sample_rate=sample_rate)
    
    # avg_blink = extractor.getBlinkScalar(mock_data)
    # nod_freq = extractor.getNodFreqScalar(mock_data)
    # avg_accel = extractor.getAvgAccelScalar(mock_data)
    # print(mock_data)
    # print(f"Average Blink Duration: {avg_blink:.2f} ms")
    # print(f"Nodding Frequency: {nod_freq:.2f} Hz")
    # print(f"Average Acceleration (ay): {avg_accel:.2f}")
