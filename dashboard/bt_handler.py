import asyncio
import random

class BluetoothModel:
    def __init__(self):
        self.connected = False
        self.client = None

    async def connect(self, mac_address=None):
        # Fake connection for now
        print(f"🔗 Simulating connection to {mac_address or 'ESP32'}...")
        await asyncio.sleep(1)
        self.connected = True
        print("✅ Connected.")
        return True

    def check_connection(self):
        return self.connected

    async def read_data(self, callback):
        # Fake sensor data stream for now
        while self.connected:
            data = random.uniform(20, 100)  # fake sensor value
            await callback(data)
            await asyncio.sleep(1)  # simulate 1s sampling rate

    def disconnect(self):
        self.connected = False
        print("🔌 Disconnected.")
