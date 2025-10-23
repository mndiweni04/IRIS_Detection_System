import asyncio
import json
import websockets

class WebSocketServer:
    """Broadcasts real-time state updates from the backend to connected dashboards."""
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.clients = set()

    async def handler(self, websocket):
        """Handles new dashboard connections."""
        self.clients.add(websocket)
        print(f"[WS] Dashboard connected ({len(self.clients)} client(s))")
        try:
            async for message in websocket:
                # Optionally handle incoming dashboard messages here
                print(f"[WS] Received from dashboard: {message}")
        except Exception as e:
            print(f"[WS] Client error: {e}")
        finally:
            self.clients.remove(websocket)
            print(f"[WS] Dashboard disconnected ({len(self.clients)} remaining)")

    async def broadcast(self, state: dict):
        """Send current state to all connected dashboards."""
        if not self.clients:
            return
        data = json.dumps(state, default=str)
        await asyncio.gather(*[client.send(data) for client in self.clients])

    async def start(self):
        """Starts the WebSocket server."""
        async with websockets.serve(self.handler, self.host, self.port):
            print(f"[WS] Server running at ws://{self.host}:{self.port}")
            await asyncio.Future()  # run forever
