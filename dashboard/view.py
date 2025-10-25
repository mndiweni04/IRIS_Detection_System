import PySimpleGUI as sg
from widgets.circle_progress import CircleProgress


class DashboardView:
    def __init__(self):
        # sg.theme("DarkBlue14")  # Commented out - not available in this PySimpleGUI version


        layout = [
            [sg.Text("Iris Dashboard", key="-TITLE-", font=("Poppins", 40), text_color="white")], 
            
            [sg.Text("", size=(1, 1))],
            [sg.Text("Bluetooth: ⭕ Disconnected", key="-BT-", font=("Poppins", 16), text_color="white")],
            [sg.Text("Session ID: None", key="-SESSION-", font=("Poppins", 16), text_color="white")],
            [sg.Text("Duration: 0 sec", key="-DURATION-", font=("Poppins", 16), text_color="white")],
            [sg.Canvas(size=(150, 150), key="-CIRCLE-")],
            [sg.Button("Looking Good! 😁", key="-BUTTON-", size=(40, 2), font=("Poppins", 16),
                       button_color=("white", "green"))]
        ]


        self.window = sg.Window(
            "IRIS Dashboard",
            layout,
            size=(700, 500),
            finalize=True,
            element_justification="center",
            no_titlebar=False
        )

        self.circle_progress = CircleProgress(self.window["-CIRCLE-"], size=130)

    def set_bt_status(self, connected: bool):
        text = "🟢 Connected" if connected else "⭕ Disconnected"
        self.window["-BT-"].update(f"Bluetooth: {text}")

    def set_session_id(self, session_id):
        self.window["-SESSION-"].update(f"Session ID: {session_id}")

    def set_session_duration(self, duration):
        self.window["-DURATION-"].update(f"Duration: {duration} sec")

    def set_progress(self, value):
        self.circle_progress.set(value)

    def read(self, timeout=100):
        return self.window.read(timeout=timeout)

    def close(self):
        self.window.close()