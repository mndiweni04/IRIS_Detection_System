import pandas as pd
import numpy as np
import itertools
import logging
from scipy.signal import find_peaks

logging.basicConfig(level=logging.DEBUG)
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
    def __init__(self, sample_rate=10, blink_threshold=3500, nod_threshold=0.5):
        """
        Args:
            sample_rate: Sampling rate in Hz (ACTUAL rate from device, ~10 Hz for ESP32 with 100ms delay)
            blink_threshold: Threshold in mV for photodiode blink detection (normal ~300-500 mV, blink ~50-200 mV)
            nod_threshold: Threshold in g for gyroscope peak detection during nodding
        """
        self.sample_rate = sample_rate
        self.blink_threshold = blink_threshold
        self.nod_threshold = nod_threshold
        logger.info(f"FeatureExtractor initialized: sample_rate={sample_rate} Hz, blink_threshold={blink_threshold}, nod_threshold={nod_threshold}")

    def getBlinkScalar(self, data: pd.DataFrame) -> float:
        """
        Calculates average blink duration.
        Blink = ir_raw drops below threshold (eyes closed blocks IR).
        Returns duration in milliseconds.
        """
        if data.empty or 'ir' not in data.columns:
            return 0.0
        
        ir_values = data['ir'].to_numpy()
        logger.debug(f"IR range: {ir_values.min():.0f} - {ir_values.max():.0f}, threshold: {self.blink_threshold}")
        
        is_blinking = ir_values < self.blink_threshold
        blink_durations = []
        
        for key, group in itertools.groupby(is_blinking):
            if key:
                num_samples = len(list(group))
                duration_ms = (num_samples / self.sample_rate) * 1000
                if duration_ms >= 50:
                    blink_durations.append(duration_ms)
        
        logger.debug(f"Found {len(blink_durations)} blinks: {blink_durations}")
        return float(np.mean(blink_durations)) if blink_durations else 0.0
        

    def getNodFreqScalar(self, data: pd.DataFrame) -> float:
        """
        Calculates the nodding frequency from gyroscope data (gz axis).
        Returns the frequency in Hz.
        """
        if data.empty or 'gz' not in data.columns:
            return 0.0
        
        peaks, _ = find_peaks(np.abs(data['gz'].to_numpy()), height=self.nod_threshold, distance=self.sample_rate // 10)
        
        if len(peaks) < 2:
            return 0.0

        # Calculate frequency as number of peaks per unit time
        time_span = (peaks[-1] - peaks[0]) / self.sample_rate        
        return (len(peaks) - 1) / time_span if time_span > 0 else 0.0

    def getAvgAccelScalar(self, data: pd.DataFrame) -> float:
        """
        Calculates the average acceleration scalar (motion magnitude).
        Uses 3-axis magnitude: sqrt(ax^2 + ay^2 + az^2) - 1g (gravity compensation).
        Returns the motion energy in g.
        """
        if data.empty:
            return 0.0
        
        if all(col in data.columns for col in ['ax', 'ay', 'az']):
            ax = np.abs(data['ax'].to_numpy())
            ay = np.abs(data['ay'].to_numpy())
            az = np.abs(data['az'].to_numpy())
            mag = np.sqrt(ax**2 + ay**2 + az**2)
            return float(max(0.0, np.mean(mag) - 1.0))
        
        return 0.0

# Example usage with mock data
if __name__ == '__main__':

    # Set pandas options to display the full DataFrame
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    
    # Create a mock DataFrame representing a 10-second data window
    # sample_rate = 100
    # mock_data = pd.DataFrame({
    #     'photodiode_value': np.random.randint(900, 1100, 1000),
    #     'ay': np.random.rand(1000) * 0.5,
    #     'gz': np.zeros(1000)
    # })

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
