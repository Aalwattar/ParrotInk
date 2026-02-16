from __future__ import annotations

import queue
import threading
from typing import Any, Callable, Optional, cast

from pynput import keyboard

from engine.logging import get_logger

logger = get_logger("Interaction")


class InputMonitor:
    """
    Unified keyboard monitor that handles both hotkey detection
    and 'any-key' cancellation during recording.
    Uses a background worker thread to keep the global hook callback lean.
    """

    def __init__(
        self,
        on_press: Callable[[Any], None],
        on_release: Callable[[Any], None],
    ):
        self._on_press_callback = on_press
        self._on_release_callback = on_release
        self._any_key_callback: Optional[Callable[[Any], None]] = None
        self._is_any_key_enabled = False

        self._target_hotkey_str: Optional[str] = None
        self._target_vk: Optional[int] = None

        self._listener: Optional[keyboard.Listener] = None
        self._event_queue: queue.Queue = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def set_target_hotkey(self, hotkey_str: str):
        """Sets the hotkey string to be suppressed (e.g., 'ctrl+alt+v')."""
        self._target_hotkey_str = hotkey_str
        self._target_vk = self._parse_target_vk(hotkey_str)
        logger.debug(f"InputMonitor: Target VK for suppression set to {self._target_vk}")

    def _parse_target_vk(self, hotkey_str: str) -> Optional[int]:
        """Simple extraction of the non-modifier key VK code."""
        try:
            parts = hotkey_str.lower().split("+")
            # Filter out modifiers
            non_modifiers = [p for p in parts if p not in ("ctrl", "alt", "shift", "win")]
            if not non_modifiers:
                return None

            target = non_modifiers[-1].strip()
            if target == "space":
                return 0x20
            if len(target) == 1:
                # Character key - on Windows, VK is typically the uppercase ASCII value
                return ord(target.upper())

            # Fallback: try to let pynput parse it if it's a special key name
            # We use a dummy listener just to get the key object
            parsed_keys = keyboard.HotKey.parse(target)
            if parsed_keys:
                key = list(parsed_keys)[0]
                if hasattr(key, "vk"):
                    return cast(int, key.vk)
                if hasattr(key, "value") and hasattr(key.value, "vk"):
                    return cast(int, key.value.vk)
        except Exception as e:
            logger.error(f"Failed to parse VK for {hotkey_str}: {e}")
        return None

    def set_any_key_callback(self, callback: Callable[[Any], None]):
        """Sets the callback for when 'any key' monitoring is active."""
        self._any_key_callback = callback

    def enable_any_key_monitoring(self, enabled: bool):
        """Enables or disables 'any key' cancellation logic."""
        self._is_any_key_enabled = enabled

    def _on_press_hook(self, key):
        """Ultra-lean hook callback for pynput."""
        self._event_queue.put(("press", key))

    def _on_release_hook(self, key):
        """Ultra-lean hook callback for pynput."""
        self._event_queue.put(("release", key))

    def _win32_filter(self, msg, data):
        """Low-level Win32 hook filter to selectively suppress target hotkey."""
        # 0x100 = WM_KEYDOWN, 0x101 = WM_KEYUP
        # 0x104 = WM_SYSKEYDOWN, 0x105 = WM_SYSKEYUP
        if self._target_vk and data.vkCode == self._target_vk:
            event_type = "press" if msg in (0x100, 0x104) else "release"
            key = keyboard.KeyCode.from_vk(data.vkCode)

            # Manually queue the event because returning False stops pynput from seeing it
            self._event_queue.put((event_type, key))

            # Tell the listener to suppress this event system-wide
            if self._listener:
                self._listener.suppress_event()

            return False

        return True

    def _worker_loop(self):
        """Background thread for processing hook events."""
        while not self._stop_event.is_set():
            try:
                # Poll with timeout to check stop_event regularly
                item = self._event_queue.get(timeout=0.1)
                event_type, key = item

                if event_type == "press":
                    self._on_press_callback(key)
                    if self._is_any_key_enabled and self._any_key_callback:
                        self._any_key_callback(key)
                elif event_type == "release":
                    self._on_release_callback(key)

                self._event_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in InputMonitor worker: {e}")

    def start(self):
        """Starts the pynput listener and worker thread."""
        if self._worker_thread is None:
            self._stop_event.clear()
            self._worker_thread = threading.Thread(
                target=self._worker_loop, daemon=True, name="InteractionWorker"
            )
            self._worker_thread.start()

        if self._listener is None:
            self._listener = keyboard.Listener(
                on_press=self._on_press_hook,
                on_release=self._on_release_hook,
                win32_event_filter=self._win32_filter,
            )
            self._listener.start()
            logger.debug("InputMonitor (pynput) started with lean callbacks.")

    def stop(self):
        """Stops the pynput listener and signals worker to stop."""
        self._stop_event.set()
        if self._listener:
            self._listener.stop()
            self._listener = None

        if self._worker_thread:
            # We don't join to avoid blocking if the loop is slow
            self._worker_thread = None

        # Drain queue if needed
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
                self._event_queue.task_done()
            except queue.Empty:
                break

        logger.debug("InputMonitor stopped.")
