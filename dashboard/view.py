import PySimpleGUI as Sg
from widgets.circle_progress import CircleProgress


class DashboardView:
    def __init__(self):
        Sg.theme("DarkBlue14")


        layout = [
            [Sg.Text("Iris Dashboard", key="-TITLE-", font=("Poppins", 40), text_color="white")], 
            
            [Sg.Text("", size=(1, 1))],
            [Sg.Text("Bluetooth: ⭕ Disconnected", key="-BT-", font=("Poppins", 16), text_color="white")],
            [Sg.Text("Session ID: None", key="-SESSION-", font=("Poppins", 16), text_color="white")],
            [Sg.Text("Duration: 0 sec", key="-DURATION-", font=("Poppins", 16), text_color="white")],
            [Sg.Canvas(size=(150, 150), key="-CIRCLE-")],
            [Sg.Button("Looking Good! 😁", key="-BUTTON-", size=(40, 2), font=("Poppins", 16),
                       button_color=("white", "green"))]
        ]


        self.window = Sg.Window(
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