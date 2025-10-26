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
        self._rx_buffer = ""

    async def connect_and_subscribe(self):
        """Connect to BLE device and subscribe to TX notifications."""
        backoff = 2  # seconds
        while self._running:
            try:
                logging.info(f"Scanning for BLE device '{self.device_name}' (service filter: {SERVICE_UUID})...")
                device = None

                # Prefer service-UUID based discovery (more reliable)
                try:
                    device = await BleakScanner.find_device_by_filter(
                        lambda d, ad: SERVICE_UUID.lower() in [u.lower() for u in (ad.service_uuids or [])],
                        timeout=5.0
                    )
                except OSError as ose:
                    # Handle Windows Bluetooth device not ready error
                    if "device is not ready" in str(ose).lower() or "-2147020577" in str(ose):
                        logging.warning(f"Windows Bluetooth device not ready: {ose}. Waiting before retry...")
                        await asyncio.sleep(3)
                        continue
                    logging.debug(f"Service-filtered scan not available or failed: {ose}")
                    device = None
                except Exception as e:
                    logging.debug(f"Service-filtered scan not available or failed: {e}")
                    device = None

                # Fallback to name-based discovery with retry on device not ready
                if not device:
                    try:
                        devices = await BleakScanner.discover(timeout=5.0)
                        device = next((d for d in devices if d.name == self.device_name), None)
                    except OSError as ose:
                        if "device is not ready" in str(ose).lower() or "-2147020577" in str(ose):
                            logging.warning(f"Windows Bluetooth device not ready during fallback scan: {ose}. Waiting before retry...")
                            await asyncio.sleep(3)
                            continue
                        raise

                if not device:
                    logging.warning("Device not found. Retrying...")
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 20)
                    continue

                addr = getattr(device, "address", str(device))
                logging.info(f"Found device {getattr(device,'name', '')} @ {addr}. Connecting...")
                self.client = BleakClient(addr)
                await self.client.connect()
                logging.info("Connected to peripheral.")

                # Verify characteristic presence (Bleak API compatibility fix)
                try:
                    # Newer Bleak: services is a property
                    services = self.client.services
                except AttributeError:
                    # Older Bleak: get_services() is a method
                    services = await self.client.services()
                
                char_uuids = [c.uuid.lower() for s in services for c in s.characteristics]
                if self.tx_uuid.lower() not in char_uuids:
                    logging.warning(f"TX characteristic {self.tx_uuid} not found on device; disconnecting.")
                    await self.client.disconnect()
                    self.client = None
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 20)
                    continue

                # Subscribe to notifications
                await self.client.start_notify(self.tx_uuid, self._handle_tx_data)
                logging.info(f"Subscribed to notifications on {self.tx_uuid}")

                # Reset backoff on success
                backoff = 2

                # Remain connected until stopped or disconnected
                while self._running and getattr(self.client, "is_connected", False):
                    await asyncio.sleep(1)

                # Clean up if still connected
                if self.client:
                    try:
                        await self.client.stop_notify(self.tx_uuid)
                    except Exception as e:
                        logging.debug(f"stop_notify error: {e}")
                    try:
                        await self.client.disconnect()
                    except Exception as e:
                        logging.debug(f"disconnect error: {e}")
                    self.client = None

            except asyncio.CancelledError:
                logging.info("connect_and_subscribe cancelled.")
                break
            except Exception as e:
                logging.exception(f"BLE handler error: {e}")
                # Ensure client is disconnected on unexpected error
                try:
                    if self.client:
                        await self.client.disconnect()
                except Exception:
                    pass
                self.client = None
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 20)

        logging.info("BLE handler stopped.")

    async def stop(self):
        """Stop BLE handler and disconnect gracefully."""
        logging.info("Stopping BLE handler...")
        self._running = False
        if self.client:
            try:
                if getattr(self.client, "is_connected", False):
                    try:
                        await self.client.stop_notify(self.tx_uuid)
                    except Exception:
                        pass
                    await self.client.disconnect()
                    logging.info("BLE client disconnected.")
            except Exception as e:
                logging.warning(f"Error disconnecting client: {e}")
            finally:
                self.client = None

    def _handle_tx_data(self, sender, data: bytearray):
        """Reassemble chunks and deliver parsed JSON objects (or raw string on parse failure)."""
        try:
            chunk = data.decode("utf-8", errors="ignore")
        except Exception:
            logging.exception("Failed to decode BLE data chunk.")
            return

        text = chunk.strip()
        # Fast path: a single complete JSON object in this notification
        if text and text[0] in ("{", "["):
            try:
                payload = json.loads(text)
                self.data_callback(payload)
                return
            except json.JSONDecodeError:
                # fall back to reassembly paths
                pass

        # Append to reassembly buffer and process newline-delimited messages
        self._rx_buffer += chunk
        while "\n" in self._rx_buffer:
            line, self._rx_buffer = self._rx_buffer.split("\n", 1)
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                payload = line
            self.data_callback(payload)

        # Try to decode concatenated JSON objects without newline (best-effort)
        if self._rx_buffer:
            decoder = json.JSONDecoder()
            s = self._rx_buffer.lstrip()
            pos = 0
            consumed = 0
            while pos < len(s):
                try:
                    obj, end = decoder.raw_decode(s[pos:])
                    self.data_callback(obj)
                    pos += end
                    consumed = pos
                    # skip whitespace between objects
                    while pos < len(s) and s[pos].isspace():
                        pos += 1
                except json.JSONDecodeError:
                    break
            if consumed:
                # remove consumed prefix from buffer
                self._rx_buffer = s[consumed:].lstrip()
