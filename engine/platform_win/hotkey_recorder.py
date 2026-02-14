import threading
from typing import Callable, List, Optional, Set

from pynput import keyboard

from engine.logging import get_logger

logger = get_logger("HotkeyRecorder")


class HotkeyRecorder:
    """
    Captures a sequence of keys to define a new hotkey.
    Uses pynput for low-level hook management.
    """

    RESERVED_COMBINATIONS = [
        {"cmd", "l"},  # Lock screen
        {"alt", "f4"},  # Close window
        {"ctrl", "alt", "delete"},  # Security
        {"cmd", "r"},  # Run
    ]

    def __init__(self):
        self.current_keys: Set[str] = set()
        self.recorded_hotkey: Optional[str] = None
        self.on_captured: Optional[Callable[[str], None]] = None
        self._listener: Optional[keyboard.Listener] = None
        self._stop_event = threading.Event()

    def is_valid(self, keys: List[str]) -> bool:
        """Checks if a key combination is allowed."""
        key_set = {k.lower() for k in keys}
        
        # 1. Reject empty
        if not key_set:
            return False
            
        # 2. Reject reserved system shortcuts
        for reserved in self.RESERVED_COMBINATIONS:
            if reserved.issubset(key_set):
                return False
                
        # 3. Must have at least one modifier OR a function key
        modifiers = {"ctrl", "alt", "shift", "cmd"}
        has_modifier = any(m in key_set for m in modifiers)
        has_fkey = any(k.startswith("f") and k[1:].isdigit() for k in key_set)
        
        if not (has_modifier or has_fkey):
            # We don't want 'a' to be a hotkey.
            return False
            
        return True

    def _normalize_key(self, key: keyboard.Key | keyboard.KeyCode) -> Optional[str]:
        """Normalizes pynput key to a string string."""
        if isinstance(key, keyboard.Key):
            name = key.name
            # Map pynput names to our canonical names
            mapping = {
                "ctrl_l": "ctrl",
                "ctrl_r": "ctrl",
                "alt_l": "alt",
                "alt_r": "alt",
                "shift_l": "shift",
                "shift_r": "shift",
                "cmd_l": "cmd",
                "cmd_r": "cmd",
            }
            return mapping.get(name, name)
        elif hasattr(key, "char") and key.char:
            return key.char.lower()
        return None

    def _on_press(self, key):
        k = self._normalize_key(key)
        if k:
            self.current_keys.add(k)

    def _on_release(self, key):
        # On first release of any key, we consider the current 'pressed' set as the hotkey
        if self.current_keys:
            keys_list = sorted(list(self.current_keys))
            if self.is_valid(keys_list):
                self.recorded_hotkey = "+".join(keys_list)
                if self.on_captured:
                    self.on_captured(self.recorded_hotkey)
                self.stop()
            else:
                # If invalid, clear and wait for next try
                logger.warning(f"Invalid hotkey combination ignored: {'+'.join(keys_list)}")
                self.current_keys.clear()

    def start(self, callback: Callable[[str], None]):
        """Starts recording. Blocks until a valid hotkey is captured or stop() is called."""
        self.on_captured = callback
        self.recorded_hotkey = None
        self.current_keys.clear()
        self._stop_event.clear()

        with keyboard.Listener(on_press=self._on_press, on_release=self._on_release) as listener:
            self._listener = listener
            # We use a stop event to allow external interruption
            while not self._stop_event.is_set() and self.recorded_hotkey is None:
                self._stop_event.wait(0.1)
            
        self._listener = None

    def stop(self):
        """Interrupts recording."""
        self._stop_event.set()
        if self._listener:
            self._listener.stop()
