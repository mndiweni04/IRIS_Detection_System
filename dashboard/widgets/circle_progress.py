import math


class CircleProgress:
    def __init__(self, canvas, size=120):

        self.canvas = canvas.Widget
        self.size = size

        # Background circle
        self.bg_circle = self.canvas.create_oval(
            10, 10, size, size, outline="grey", width=10
        )

        #(progress)
        self.arc = self.canvas.create_arc(
            10, 10, size, size,
            start=90, extent=0,
            style="arc", outline="green", width=10
        )

    def set(self, value: float):
        """Set progress value between 0 and 1"""
        value = max(0, min(1, value))
        extent = -value * 360  # Clockwise
        self.canvas.itemconfig(self.arc, extent=extent)


