import asyncio
import json
import websockets
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class DashboardWebSocketClient:
    """Connects to backend WebSocket server to receive live updates."""
    def __init__(self, uri="ws://localhost:8765"):
        self.uri = uri
        self.on_message: Optional[Callable] = None
        self._backoff = 2  # Initial backoff in seconds

    async def listen(self):
        """Connect and listen for messages, with connection retry logic."""
        while True:
            try:
                logger.info(f"[WS] Attempting to connect to {self.uri}")
                async with websockets.connect(
                    self.uri,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=10,
                ) as ws:
                    logger.info(f"[WS] Connected to backend at {self.uri}")
                    self._backoff = 2  # Reset backoff on successful connection
                    
                    try:
                        async for msg in ws:
                            try:
                                data = json.loads(msg)
                                if self.on_message is not None:
                                    logger.debug(f"[WS] Received data: {data}")
                                    self.on_message(data)
                            except json.JSONDecodeError:
                                logger.warning(f"[WS] Invalid JSON received: {msg}")
                    except asyncio.CancelledError:
                        logger.info("[WS] Connection listener cancelled")
                        raise
                    
            except websockets.exceptions.WebSocketException as e:
                logger.warning(f"[WS] WebSocket error: {e}")
            except (OSError, asyncio.TimeoutError) as e:
                logger.warning(f"[WS] Connection error: {e}")
            except asyncio.CancelledError:
                logger.info("[WS] Listener cancelled")
                raise
            except Exception as e:
                logger.error(f"[WS] Unexpected error: {e}", exc_info=True)
            
            # Exponential backoff with max 30 seconds
            wait_time = min(self._backoff, 30)
            logger.info(f"[WS] Retrying connection in {wait_time} seconds...")
            try:
                await asyncio.sleep(wait_time)
            except asyncio.CancelledError:
                logger.info("[WS] Sleep cancelled")
                raise
            
            self._backoff = min(self._backoff * 1.5, 30)

    def start(self):
        """Creates a new event loop and runs the listener in this thread."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            logger.info("[WS] Client listener thread started")
            loop.run_until_complete(self.listen())
            
        except KeyboardInterrupt:
            logger.info("[WS] WebSocket client stopped by user")
        except asyncio.CancelledError:
            logger.info("[WS] WebSocket client cancelled")
        except (RuntimeError, OSError) as e:
            logger.error(f"[WS] Client loop failed: {e}", exc_info=True)
        finally:
            try:
                # Clean up remaining tasks
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            finally:
                loop.close()
                logger.info("[WS] Client listener thread stopped")