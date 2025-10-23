import asyncio
import json
import websockets

class DashboardWebSocketClient:
    """Connects to backend WebSocket server to receive live updates."""
    def __init__(self, uri="ws://localhost:8765"):
        self.uri = uri
        self.on_message = None

    async def listen(self):
        """Connect and listen for messages, with connection retry logic."""
        try:
            async with websockets.connect(self.uri) as ws:
                print(f"[WS] Connected to backend at {self.uri}")
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    if self.on_message:
                        self.on_message(data)
        except Exception as e:
            print(f"[WS] Connection error: {e}. Retrying in 2 seconds...")
            await asyncio.sleep(2)
            await self.listen()

    def start(self):
        """Creates a new event loop and runs the listener in this thread."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            print("[WS] Client listener thread started.")
            
            loop.run_until_complete(self.listen())
            
        except KeyboardInterrupt:
            print("[WS] WebSocket client stopped.")
        except Exception as e:
            print(f"[WS] Client loop failed: {e}")
        finally:
            if 'loop' in locals() and loop.is_running():
                for task in asyncio.all_tasks(loop=loop):
                    task.cancel()