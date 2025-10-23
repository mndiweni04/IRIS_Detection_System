# run_dashboard.py

import asyncio
from bt_handler import scan_devices, connect_by_mac, read_payload_stream
from csv_writer import CSVLogger
from config import CHARACTERISTIC_UUID

async def main():
    logger = CSVLogger()
    try:
        devices = await scan_devices()

        # Prompt user to select device by index
        index = int(input("\nEnter device number to connect: ")) - 1
        selected = devices[index]
        mac = selected.address

        client = await connect_by_mac(mac)
        await read_payload_stream(client, CHARACTERISTIC_UUID, logger.log)

    except Exception as e:
        print(f"❌ Failed: {e}")
    finally:
        logger.close()

if __name__ == "__main__":
    asyncio.run(main())
