from typing import Callable, Optional

from pynput import mouse

from engine.logging import get_logger

logger = get_logger("MouseMonitor")


class MouseMonitor:
    """
    Monitors global mouse events to detect clicks outside the anchor.
    """

    def __init__(self, on_click_event: Callable[[int, int], None]):
        self.on_click_event = on_click_event
        self.listener: Optional[mouse.Listener] = None
        self._is_running = False

    def start(self):
        """Starts the global mouse listener."""
        if self._is_running:
            return

        logger.debug("Starting mouse monitor")
        self.listener = mouse.Listener(on_click=self._on_click)
        self.listener.start()
        self._is_running = True

    def stop(self):
        """Stops the global mouse listener."""
        if not self._is_running:
            return

        logger.debug("Stopping mouse monitor")
        if self.listener:
            self.listener.stop()
            self.listener = None
        self._is_running = False

    def _on_click(self, x: float, y: float, button: mouse.Button, pressed: bool):
        """Callback for mouse click events."""
        # We only care about Left Click Press
        if button == mouse.Button.left and pressed:
            logger.debug(f"Left click detected at ({x}, {y})")
            # We pass int coordinates to the callback
            self.on_click_event(int(x), int(y))
