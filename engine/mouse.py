"""Observe click-away actions without intercepting desktop mouse input."""

import ctypes
import threading
from ctypes import wintypes
from typing import Callable, Optional

from engine.logging import get_logger

logger = get_logger("MouseMonitor")

# Private function objects prevent other ctypes consumers from altering our ABI.
_user32 = ctypes.WinDLL("user32", use_last_error=True)
_get_button_state = _user32.GetAsyncKeyState
_get_button_state.argtypes = [ctypes.c_int]
_get_button_state.restype = wintypes.SHORT
_get_cursor_pos = _user32.GetCursorPos
_get_cursor_pos.argtypes = [ctypes.POINTER(wintypes.POINT)]
_get_cursor_pos.restype = wintypes.BOOL
_get_foreground_window = _user32.GetForegroundWindow
_get_foreground_window.argtypes = []
_get_foreground_window.restype = wintypes.HWND
_VK_LBUTTON = 0x01


def _read_button() -> bool:
    # Use current state, not the shared "pressed since read" bit.
    return bool(_get_button_state(_VK_LBUTTON) & 0x8000)


def _read_position() -> tuple[int, int] | None:
    point = wintypes.POINT()
    if not _get_cursor_pos(ctypes.byref(point)):
        return None
    return point.x, point.y


def _read_foreground() -> int:
    return int(_get_foreground_window() or 0)


class MouseMonitor:
    """Poll left-button transitions; never register or suppress input hooks."""

    POLL_INTERVAL = 0.04
    STOP_TIMEOUT = 1.0

    def __init__(self, on_click_event: Callable[[int, int], None]):
        self.on_click_event = on_click_event
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._is_running = False

    def start(self):
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._is_running = True
            self._thread = threading.Thread(target=self._poll, name="MouseStatePoller", daemon=True)
            try:
                self._thread.start()
            except Exception:
                self._is_running = False
                self._thread = None
                raise
        logger.debug("Started mouse state polling (no input hook)")

    def stop(self):
        with self._lock:
            self._stop_event.set()
            thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=self.STOP_TIMEOUT)
        with self._lock:
            if thread is not None and thread.is_alive():
                # Retain the reference and stop request to prevent a second worker.
                if thread is not threading.current_thread():
                    logger.warning("Mouse state poller did not finish before stop timeout")
            elif self._thread is thread:
                self._thread = None
                self._is_running = False

    def _poll(self):
        previous = None
        previous_foreground = None
        try:
            while not self._stop_event.is_set():
                try:
                    pressed = _read_button()
                    foreground = _read_foreground()
                    # Ignore an already-held button when establishing the baseline.
                    clicked = previous is False and pressed
                    previous = pressed
                    # A short click may begin and end between button samples.
                    # A resulting focus change survives until the next sample.
                    focus_changed = (
                        previous_foreground is not None
                        and foreground != 0
                        and foreground != previous_foreground
                    )
                    previous_foreground = foreground
                    if clicked or focus_changed:
                        position = _read_position()
                        if position is not None and not self._stop_event.is_set():
                            self.on_click_event(*position)
                except Exception:
                    logger.exception("Mouse state polling callback failed")
                    previous = None
                    previous_foreground = None
                if self._stop_event.wait(self.POLL_INTERVAL):
                    break
        finally:
            with self._lock:
                self._is_running = False
            logger.debug("Mouse state poller exited")
