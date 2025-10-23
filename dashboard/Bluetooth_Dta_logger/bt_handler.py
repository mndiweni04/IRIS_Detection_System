# bt_handler.py

import asyncio
from bleak import BleakScanner, BleakClient

async def scan_devices():
    print("🔍 Scanning for BLE devices...")
    devices = await BleakScanner.discover(timeout=10)
    print("\n📋 Available Devices:")
    for i, d in enumerate(devices):
        print(f"{i+1}. Name: {d.name or 'Unknown'} | MAC: {d.address}")
    return devices

async def connect_by_mac(mac_address):
    print(f"🔗 Attempting to connect to {mac_address}...")
    client = BleakClient(mac_address)
    await client.connect()
    print("✅ Connected.")
    return client

async def read_payload_stream(client, char_uuid, callback):
    while True:
        try:
            data = await client.read_gatt_char(char_uuid)
            await callback(data)
        except Exception as e:
            print(f"⚠️ Error reading data: {e}")
            break
