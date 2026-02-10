import time
from typing import Any


class ShutdownHandler:
    """Manages double-press Ctrl+C confirmation logic."""

    def __init__(self, window: float = 3.0):
        self.window = window
        self.last_press_time = 0.0
        self.shutdown_pending = False
        self.should_exit = False

    def handle(self, sig: Any, frame: Any) -> None:
        """Handles the SIGINT signal."""
        current_time = time.time()

        if self.shutdown_pending and (current_time - self.last_press_time <= self.window):
            print("\nForce Shutting down...", flush=True)
            self.should_exit = True
            # Force exit immediately on second press
            import os
            os._exit(1)
        else:
            print("\nCtrl+C received. Press Ctrl+C again within 3 seconds to force exit.", flush=True)
            self.shutdown_pending = True
            self.last_press_time = current_time
