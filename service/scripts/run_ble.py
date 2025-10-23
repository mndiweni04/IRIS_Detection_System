#!/usr/bin/env python3
"""
Simple BLE handler runner for testing.
Connects to the AntiSleep-Glasses transmitter and streams payloads.
"""
import asyncio
import logging
import json
from pathlib import Path
from src.bluetooth.ble_handler import BLEHandler
from src.config import DEVICE_NAME, TX_CHAR_UUID

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

async def main(runtime_s: int = 60):
    """Run BLE handler for specified duration."""
    received_count = 0
    
    def callback(payload):
        nonlocal received_count
        received_count += 1
        if isinstance(payload, dict):
            logger.info(f"[{received_count}] RECV JSON: {json.dumps(payload)}")
        else:
            logger.info(f"[{received_count}] RECV RAW: {str(payload)}")

    handler = BLEHandler(data_callback=callback)
    task = asyncio.create_task(handler.connect_and_subscribe())
    
    try:
        logger.info(f"Running BLE handler for {runtime_s}s...")
        await asyncio.sleep(runtime_s)
    finally:
        logger.info(f"Received {received_count} payloads total.")
        await handler.stop()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(main())
