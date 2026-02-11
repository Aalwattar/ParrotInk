import threading
import tkinter as tk

from engine.logging import get_logger

logger = get_logger("IndicatorUI")


class FloatingIndicator:
    """
    A small, borderless, circular floating window that reflects recording state.
    """

    def __init__(
        self, x: int = 500, y: int = 50, opacity_idle: float = 0.3, opacity_active: float = 0.8
    ):
        self.x = x
        self.y = y
        self.opacity_idle = opacity_idle
        self.opacity_active = opacity_active
        self.is_recording = False

        self.root = None
        self.canvas = None
        self.circle = None

        # Dragging state
        self._drag_start_x = 0
        self._drag_start_y = 0

        # Animation state
        self._pulse_direction = 1
        self._pulse_alpha = opacity_idle

        # Ready event
        self._ready_event = threading.Event()

    def _setup_ui(self):
        """Initializes the Tkinter widgets. Must be called from the same thread as mainloop."""
        self.root = tk.Tk()
        self.root.title("Voice2Text Indicator")

        # Window properties
        self.root.overrideredirect(True)  # Remove title bar and borders
        self.root.attributes("-topmost", True)  # Always on top
        self.root.attributes("-alpha", self.opacity_idle)  # Transparency

        # Dimensions
        self.size = 30
        self.root.geometry(f"{self.size}x{self.size}+{self.x}+{self.y}")

        # Canvas for drawing
        self.canvas = tk.Canvas(
            self.root, width=self.size, height=self.size, highlightthickness=0, bg="black"
        )
        self.canvas.pack()

        # Make it look like a circle
        self.root.config(bg="black")
        self.root.attributes("-transparentcolor", "black")

        self.circle = self.canvas.create_oval(
            2, 2, self.size - 2, self.size - 2, fill="gray", outline="white", width=2
        )

        # Dragging logic
        self.root.bind("<Button-1>", self._start_drag)
        self.root.bind("<B1-Motion>", self._do_drag)
        self.root.bind("<ButtonRelease-1>", self._stop_drag)

        # Initial state
        if self.is_recording:
            self.set_recording(True)

    def _start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _do_drag(self, event):
        x = self.root.winfo_x() + event.x - self._drag_start_x
        y = self.root.winfo_y() + event.y - self._drag_start_y
        self.root.geometry(f"+{x}+{y}")

    def _stop_drag(self, event):
        logger.debug(f"Indicator moved to ({self.root.winfo_x()}, {self.root.winfo_y()})")

    def set_recording(self, recording: bool):
        """Updates the visual state. Safe to call from any thread via after()."""
        self.is_recording = recording
        if not self.root:
            return

        # Use root.after to ensure thread safety if called from elsewhere
        def _update():
            if recording:
                self.canvas.itemconfig(self.circle, fill="red", outline="white")
                self.root.attributes("-alpha", self.opacity_active)
                self._animate_pulse()
            else:
                self.canvas.itemconfig(self.circle, fill="gray", outline="white")
                self.root.attributes("-alpha", self.opacity_idle)

        try:
            self.root.after(0, _update)
        except Exception:
            pass

    def _animate_pulse(self):
        """Pulsing animation while recording."""
        if not self.is_recording or not self.root:
            return

        try:
            current_alpha = float(self.root.attributes("-alpha"))
            step = 0.05

            if self._pulse_direction > 0:
                new_alpha = min(self.opacity_active, current_alpha + step)
                if new_alpha >= self.opacity_active:
                    self._pulse_direction = -1
            else:
                new_alpha = max(self.opacity_idle + 0.2, current_alpha - step)
                if new_alpha <= self.opacity_idle + 0.2:
                    self._pulse_direction = 1

            self.root.attributes("-alpha", new_alpha)
            self.root.after(50, self._animate_pulse)
        except Exception:
            pass

    def run(self):
        """Starts the Tkinter main loop."""
        self._setup_ui()
        self._ready_event.set()
        self.root.mainloop()

    def stop(self):
        """Closes the indicator window."""
        if self.root:
            self.root.after(0, self.root.destroy)
