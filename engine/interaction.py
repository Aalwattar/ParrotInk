from typing import Callable, Optional
from pynput import keyboard

class InteractionMonitor:
    def __init__(self):
        self._any_key_callback: Optional[Callable[[], None]] = None
        self._listener: Optional[keyboard.Listener] = None

    def set_any_key_callback(self, callback: Callable[[], None]):
        self._any_key_callback = callback

    def _on_press(self, key):
        if self._any_key_callback:
            self._any_key_callback()

    def start(self):
        if self._listener is None:
            self._listener = keyboard.Listener(on_press=self._on_press)
            self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener = None
