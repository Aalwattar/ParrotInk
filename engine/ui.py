import signal
import threading
from enum import Enum
from typing import Callable

import pystray
from PIL import Image, ImageDraw


class AppState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    ERROR = "error"


class TrayApp:
    def __init__(self, on_quit_callback: Callable | None = None):
        self.state = AppState.IDLE
        self.on_quit_callback = on_quit_callback
        self.icon = self._create_icon()
        self._setup_signal_handlers()

    def _create_image(self, color: str) -> Image.Image:
        # Create a simple icon based on the state color
        width, height = 64, 64
        image = Image.new("RGB", (width, height), "white")
        dc = ImageDraw.Draw(image)
        dc.ellipse((8, 8, 56, 56), fill=color)
        return image

    def _get_icon_color(self, state: AppState) -> str:
        if state == AppState.LISTENING:
            return "red"
        if state == AppState.ERROR:
            return "orange"
        return "black"

    def _create_icon(self) -> pystray.Icon:
        menu = pystray.Menu(
            pystray.MenuItem("Status: Ready", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self.stop),
        )

        return pystray.Icon(
            "voice2text", self._create_image(self._get_icon_color(self.state)), "Voice2Text", menu
        )

    def _setup_signal_handlers(self) -> None:
        # Handle Ctrl+C in the terminal
        signal.signal(signal.SIGINT, lambda sig, frame: self.stop())

    def set_state(self, state: AppState) -> None:
        self.state = state
        self.icon.icon = self._create_image(self._get_icon_color(state))
        # Update status menu item would require recreating or complex menu manipulation
        # For now, we focus on the icon color change

    def run(self) -> None:
        """Starts the tray icon. This call is blocking."""
        self.icon.run()

    def stop(self) -> None:
        """Stops the tray icon and triggers clean shutdown."""
        print("\nShutting down cleanly...")
        self.icon.stop()
        if self.on_quit_callback:
            self.on_quit_callback()


class TrayAppThread(threading.Thread):
    """Utility to run the TrayApp in a non-blocking thread."""

    def __init__(self, app: TrayApp):
        super().__init__()
        self.app = app
        self.daemon = True

    def run(self) -> None:
        self.app.run()
