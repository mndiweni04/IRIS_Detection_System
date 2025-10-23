import time
import random
import PySimpleGUI as Sg
import threading
from view import DashboardView
from ws_client import DashboardWebSocketClient


class ButtonController:
    """Controls button text, color, and window background based on driver state."""
    def __init__(self, window, circle_progress):
        self.window = window
        self.circle_progress = circle_progress

    def update(self, driver_state):
        """Update button, progress, circle, and window colors based on driver state."""
        if driver_state == "awake":
            text = "Alert,Looking Good! 😁"
            color = "green"

            progress = 1.0
        elif driver_state == "sleepy":
            text = "Fatigue detected,Be Careful! 😐"
            color = "#ffc40c"

            progress = 0.5
        elif driver_state == "idle":
            text = "Awaiting Data/Hardware"
            color = "gray"
            progress = 0.0
        else:
            text = "Drowsy,Danger😴"
            color = "red"
            progress = 0.1

        self.window["-BUTTON-"].update(text=text, button_color=("white", color))
        self.circle_progress.set(progress)

class DashboardController:
    def __init__(self):
        self.view = DashboardView()
        self.session_start_time = time.time()
        
        self._running = True

        self.button_ctrl = ButtonController(self.view.window, self.view.circle_progress)

        self.ws_client = DashboardWebSocketClient()
        self.ws_client.on_message = self.handle_backend_update

        threading.Thread(target=self.ws_client.start, daemon=True).start()


    def run(self):
        try:
            while self._running:
                event, values = self.view.read(timeout=100)

                if event in (Sg.WINDOW_CLOSED, "Exit"):
                    self._running = False
                    break

                if event == "-WS_UPDATE-" and isinstance(values, dict) and "status" in values:
                    status = values["status"]
                    connected = values["connected"]
                    duration = values["duration"]
                    session_id = values.get("session_id", "None") 

                    self.view.set_bt_status(connected)
                    self.view.set_session_duration(int(duration))
                    self.view.set_session_id(session_id) 

                    if status == "Looking good":
                        driver_state = "awake"
                    elif status == "Be careful":
                        driver_state = "sleepy"
                    elif status in ("Awaiting Data", "Awaiting Hardware"):
                        driver_state = "idle"
                    else:
                        driver_state = "falling_asleep"

                    self.button_ctrl.update(driver_state)

            self.view.close()
        except KeyboardInterrupt:
            self.view.close()

    def handle_backend_update(self, state):
        """Receive state from backend and post an event to the GUI thread."""
        connected = state.get("connected", False)
        duration = state.get("duration", 0)
        status = state.get("status", "Unknown")
        session_id = state.get("session_id", "None")

        self.view.window.write_event_value(
            "-WS_UPDATE-",
            {"status": status, "connected": connected, "duration": duration, "session_id": session_id}
        )