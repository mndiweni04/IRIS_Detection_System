import asyncio
import json
import websockets
import logging

logger = logging.getLogger(__name__)


class WebSocketServer:
    """Broadcasts real-time state updates from the backend to connected dashboards."""
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.clients = set()

    async def handler(self, websocket, path=None):
        """Handles new dashboard connections with proper error handling."""
        self.clients.add(websocket)
        logger.info(f"[WS] Dashboard connected ({len(self.clients)} client(s))")
        try:
            async for message in websocket:
                # Optionally handle incoming dashboard messages here
                logger.debug(f"[WS] Received from dashboard: {message}")
        except websockets.exceptions.ConnectionClosed:
            logger.debug("[WS] Connection closed normally")
        except asyncio.CancelledError:
            logger.debug("[WS] Connection cancelled")
        except Exception as e:
            logger.warning(f"[WS] Client error: {type(e).__name__}: {e}")
        finally:
            self.clients.discard(websocket)
            logger.info(f"[WS] Dashboard disconnected ({len(self.clients)} remaining)")

    async def broadcast(self, state: dict):
        """Send current state to all connected dashboards."""
        if not self.clients:
            return
        
        data = json.dumps(state, default=str)
        
        # Send to all clients, remove disconnected ones
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(data)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                logger.debug(f"[WS] Broadcast error: {e}")
                disconnected.add(client)
        
        # Clean up disconnected clients
        self.clients -= disconnected

    async def start(self):
        """Starts the WebSocket server with proper configuration."""
        try:
            async with websockets.serve(
                self.handler,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10,
            ):
                logger.info(f"[WS] Server running at ws://{self.host}:{self.port}")
                await asyncio.Future()  # run forever
        except Exception as e:
            logger.error(f"[WS] Server error: {e}", exc_info=True)
