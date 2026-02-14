import sys
from typing import Callable, Optional

from pynput import keyboard


class InputMonitor:
    """
    Unified keyboard monitor that handles both hotkey detection
    and 'any-key' cancellation during recording.
    """

    def __init__(
        self,
        on_press: Callable[[keyboard.Key | keyboard.KeyCode], None],
        on_release: Callable[[keyboard.Key | keyboard.KeyCode], None],
    ):
        self._on_press_callback = on_press
        self._on_release_callback = on_release
        self._any_key_callback: Optional[Callable[[keyboard.Key | keyboard.KeyCode], None]] = None
        self._listener: Optional[keyboard.Listener] = None
        self._is_any_key_enabled = False

    def set_any_key_callback(self, callback: Callable[[keyboard.Key | keyboard.KeyCode], None]):
        """Sets the callback for when 'any key' monitoring is active."""
        self._any_key_callback = callback

    def enable_any_key_monitoring(self, enabled: bool = True):
        """Enables or disables 'any key' cancellation logic."""
        self._is_any_key_enabled = enabled

    def _on_press(self, key):
        try:
            # 1. Always trigger the primary on_press for hotkey logic
            self._on_press_callback(key)

            # 2. If 'any-key' monitoring is active, trigger the secondary callback
            if self._is_any_key_enabled and self._any_key_callback:
                self._any_key_callback(key)
        except Exception as e:
            # Prevent listener thread from crashing
            print(f"Error in keyboard listener: {e}", file=sys.stderr)

    def _on_release(self, key):
        try:
            self._on_release_callback(key)
        except Exception as e:
            print(f"Error in keyboard listener (release): {e}", file=sys.stderr)

    def start(self):
        """Starts the global keyboard listener."""
        if self._listener is None:
            self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
            self._listener.start()

    def stop(self):
        """Stops the global keyboard listener."""
        if self._listener:
            self._listener.stop()
            self._listener = None
