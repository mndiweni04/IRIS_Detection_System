import asyncio
from bleak import BleakScanner

async def scan():
    print("🔍 Scanning...")
    devices = await BleakScanner.discover(timeout=10)
    for d in devices:
        print(f"Name: {d.name or 'Unknown'} | MAC: {d.address}")

asyncio.run(scan())
