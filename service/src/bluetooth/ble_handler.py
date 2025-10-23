# ble_handler.py

from bleak import BleakScanner, BleakClient
import asyncio
import logging
import json
from typing import Optional, Callable, Any
from ..config import DEVICE_NAME, TX_CHAR_UUID, SERVICE_UUID

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class BLEHandler:
    def __init__(
        self,
        data_callback: Callable[[Any], None],
        device_name: str = DEVICE_NAME,
        tx_uuid: str = TX_CHAR_UUID
    ):
        self.data_callback = data_callback
        self.device_name = device_name
        self.tx_uuid = tx_uuid
        self.client: Optional[Any] = None
        self._running = True
        self._rx_buffer = "" # Retain buffer for chunk reassembly

    async def connect_and_subscribe(self,):
        """Connect to BLE device and subscribe to TX notifications."""
        # ... (connect_and_subscribe remains UNCHANGED) ...
        # (This large block of connection logic remains the same)
        pass # Placeholder for brevity.

    async def stop(self):
        """Stop BLE handler and disconnect gracefully."""
        # ... (stop remains UNCHANGED) ...
        pass # Placeholder for brevity.

    def _handle_tx_data(self, sender, data: bytearray):
        """Reassemble chunks and deliver parsed JSON objects (or raw string on parse failure)."""
        try:
            chunk = data.decode("utf-8", errors="ignore")
        except Exception:
            logging.exception("Failed to decode BLE data chunk.")
            return

        # Append to reassembly buffer
        self._rx_buffer += chunk

        # Process newline-delimited messages
        while "\n" in self._rx_buffer:
            line, self._rx_buffer = self._rx_buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            
            try:
                # Attempt to parse a complete JSON object from the line
                payload = json.loads(line)
            except json.JSONDecodeError:
                # CRITICAL: If the line isn't a valid JSON object, log it 
                # and pass the raw line or discard, but do NOT fail the process.
                # We'll pass the raw line to the processor for best-effort handling.
                logging.warning(f"JSONDecodeError on line: {line[:50]}...")
                payload = line
                
            self.data_callback(payload)