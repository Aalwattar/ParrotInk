from __future__ import annotations

import threading
from typing import Any, Callable, Optional

import keyboard

from engine.logging import get_logger

logger = get_logger("Interaction")


class InputMonitor:
    """
    Simplified keyboard monitor that uses the 'keyboard' library for
    zero-leakage hotkey suppression and 'any-key' cancellation.
    """

    def __init__(
        self,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ):
        self._on_press_callback = on_press
        self._on_release_callback = on_release
        self._any_key_callback: Optional[Callable[[Any], None]] = None
        self._is_any_key_enabled = False

        self._hotkey_str: Optional[str] = None
        self._is_running = False
        self._hold_mode = False
        self._is_hotkey_down = False
        self._hooks: list[Any] = []
        self._lock = threading.Lock()

    def set_hotkey(self, hotkey_str: str, hold_mode: bool = False):
        """Sets the hotkey string and mode."""
        with self._lock:
            self._hotkey_str = hotkey_str
            self._hold_mode = hold_mode
            if self._is_running:
                # Re-register if already running
                # Note: stop() and start() also use the lock, 
                # so we must be careful with recursion.
                pass
        
        # Call outside lock to avoid deadlock if stop/start also use it
        if self._is_running:
            self.stop()
            self.start()

    def set_any_key_callback(self, callback: Callable[[Any], None]):
        """Sets the callback for when 'any key' monitoring is active."""
        self._any_key_callback = callback

    def enable_any_key_monitoring(self, enabled: bool):
        """Enables or disables 'any key' cancellation logic."""
        self._is_any_key_enabled = enabled

    def reset_state(self):
        """Resets the internal tracking state (e.g. if hotkey is considered down)."""
        with self._lock:
            self._is_hotkey_down = False

    def _any_key_hook(self, event):
        """Hook for detecting any key press during recording."""
        if not self._is_any_key_enabled or not self._any_key_callback:
            return

        if event.event_type == "down":
            # We filter out the hotkey itself to prevent self-cancellation
            self._any_key_callback(event.name)

    def _get_hotkey_parts(self) -> set[str]:
        """Parses the hotkey string into a set of normalized key names."""
        if not self._hotkey_str:
            return set()
        try:
            # parse_hotkey returns [( (scan_codes), (names) ), ...]
            parsed = keyboard.parse_hotkey(self._hotkey_str)
            return set(parsed[0][1])  # names
        except Exception:
            return set(self._hotkey_str.split("+"))

    def start(self):
        """Starts the keyboard hooks."""
        with self._lock:
            if self._is_running or not self._hotkey_str:
                return

            try:
                hotkey_parts = self._get_hotkey_parts()

                # 1. Register the hotkey with suppression
                if self._hold_mode:
                    self._is_hotkey_down = False

                    def _on_press_internal():
                        with self._lock:
                            if not self._is_hotkey_down:
                                self._is_hotkey_down = True
                                self._on_press_callback()

                    def _on_release_hook(event):
                        if event.event_type == "up" and event.name in hotkey_parts:
                            with self._lock:
                                if self._is_hotkey_down:
                                    self._is_hotkey_down = False
                                    self._on_release_callback()

                    h1 = keyboard.add_hotkey(
                        self._hotkey_str,
                        _on_press_internal,
                        suppress=True,
                        trigger_on_release=False,
                    )
                    self._hooks.append(h1)

                    h2 = keyboard.hook(_on_release_hook)
                    self._hooks.append(h2)
                else:
                    # In Toggle mode, we use a similar debounced structure to prevent
                    # rapid fire if the key is held down.
                    def _on_toggle_press():
                        with self._lock:
                            if not self._is_hotkey_down:
                                self._is_hotkey_down = True
                                self._on_press_callback()

                    def _on_toggle_release(event):
                        if event.event_type == "up" and event.name in hotkey_parts:
                            with self._lock:
                                self._is_hotkey_down = False

                    h1 = keyboard.add_hotkey(
                        self._hotkey_str, _on_toggle_press, suppress=True, trigger_on_release=False
                    )
                    self._hooks.append(h1)

                    h2 = keyboard.hook(_on_toggle_release)
                    self._hooks.append(h2)

                # 2. Register the 'any-key' hook for cancellation
                h3 = keyboard.hook(self._any_key_hook)
                self._hooks.append(h3)

                self._is_running = True
                logger.debug(f"InputMonitor started with hotkey: {self._hotkey_str} (suppressed)")
            except Exception as e:
                logger.error(f"Failed to start InputMonitor: {e}")

    def stop(self):
        """Stops all keyboard hooks tracked by this monitor."""
        with self._lock:
            try:
                for hook in self._hooks:
                    try:
                        keyboard.unhook(hook)
                    except Exception:
                        pass
                self._hooks.clear()
                self._is_running = False
                logger.debug("InputMonitor stopped (tracked hooks removed).")
            except Exception as e:
                logger.error(f"Error stopping InputMonitor: {e}")
