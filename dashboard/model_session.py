class SessionModel:
    def __init__(self):
        self.current_session_id = 1

    def save_session(self, duration_seconds):
        print(f"[SessionModel] Session {self.current_session_id} saved: {duration_seconds:.1f} sec")
        self.current_session_id += 1
