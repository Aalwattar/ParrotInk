"""Observe native click events without consuming desktop mouse input."""

import ctypes
import queue
import threading
from ctypes import wintypes
from typing import Callable, Optional

from engine.logging import get_logger
from engine.platform_win.dpi import physical_coordinates
from engine.platform_win.keys import HOOKPROC

logger = get_logger("MouseMonitor")

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_set_hook = _user32.SetWindowsHookExW
_set_hook.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
_set_hook.restype = wintypes.HHOOK
_unhook = _user32.UnhookWindowsHookEx
_unhook.argtypes = [wintypes.HHOOK]
_unhook.restype = wintypes.BOOL
_next_hook = _user32.CallNextHookEx
_next_hook.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
_next_hook.restype = wintypes.LPARAM
_peek_message = _user32.PeekMessageW
_peek_message.argtypes = [
    ctypes.POINTER(wintypes.MSG),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT,
    wintypes.UINT,
]
_peek_message.restype = wintypes.BOOL
_get_cursor_pos = _user32.GetPhysicalCursorPos
_get_cursor_pos.argtypes = [ctypes.POINTER(wintypes.POINT)]
_get_cursor_pos.restype = wintypes.BOOL
_get_foreground_window = _user32.GetForegroundWindow
_get_foreground_window.argtypes = []
_get_foreground_window.restype = wintypes.HWND

WH_MOUSE_LL = 14
WM_LBUTTONDOWN = 0x0201


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


@physical_coordinates()
def _read_position() -> tuple[int, int] | None:
    point = wintypes.POINT()
    if not _get_cursor_pos(ctypes.byref(point)):
        return None
    return point.x, point.y


def _read_foreground() -> int:
    return int(_get_foreground_window() or 0)


class MouseMonitor:
    """Pump a passive mouse hook; run cancellation after the hook returns."""

    POLL_INTERVAL = 0.02
    STOP_TIMEOUT = 1.0

    def __init__(self, on_click_event: Callable[[int, int], None]):
        self.on_click_event = on_click_event
        self._thread: Optional[threading.Thread] = None
        self._callback_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._ready = threading.Event()
        self._lock = threading.Lock()
        self._is_running = False
        self._hook = None
        self._hook_proc = None
        self._clicks: queue.Queue[tuple[int, int]] = queue.Queue()
        self._start_error: Optional[str] = None

    def start(self):
        with self._lock:
            if any(t and t.is_alive() for t in (self._thread, self._callback_thread)):
                if self._stop_event.is_set():
                    raise OSError("Previous mouse monitor is still stopping")
                return
            self._stop_event.clear()
            self._ready.clear()
            self._start_error = None
            self._clicks = queue.Queue()
            self._is_running = True
            self._thread = threading.Thread(target=self._poll, name="MouseMonitor", daemon=True)
            try:
                self._thread.start()
            except Exception:
                self._is_running = False
                self._thread = None
                raise
        if not self._ready.wait(self.STOP_TIMEOUT) or self._start_error:
            self.stop()
            raise OSError(self._start_error or "Mouse monitor did not start in time")

    def stop(self):
        with self._lock:
            self._stop_event.set()
            thread = self._thread
            callback_thread = self._callback_thread
        for worker in (thread, callback_thread):
            if worker is not None and worker is not threading.current_thread():
                worker.join(timeout=self.STOP_TIMEOUT)
        with self._lock:
            if any(t and t.is_alive() for t in (thread, callback_thread)):
                if thread is not threading.current_thread():
                    logger.warning("Mouse monitor did not finish before stop timeout")
            elif self._thread is thread:
                self._thread = None
                self._callback_thread = None
                self._is_running = False

    def _on_native_mouse(self, code: int, message: int, address: int):
        try:
            if code >= 0 and message == WM_LBUTTONDOWN and not self._stop_event.is_set():
                event = ctypes.cast(address, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                self._clicks.put((event.pt.x, event.pt.y))
        except Exception:
            logger.exception("Mouse event observation failed")
        # Never consume input, including when our callback or parsing fails.
        return _next_hook(self._hook, code, message, address)

    def _notify(self, position):
        if position is not None and not self._stop_event.is_set():
            try:
                self.on_click_event(*position)
            except Exception:
                logger.exception("Mouse cancellation callback failed")

    def _dispatch_clicks(self):
        while not self._stop_event.is_set():
            try:
                self._notify(self._clicks.get(timeout=0.1))
            except queue.Empty:
                continue

    @physical_coordinates()
    def _poll(self):
        previous_foreground = None
        msg = wintypes.MSG()
        try:
            _peek_message(ctypes.byref(msg), None, 0, 0, 0)
            self._hook_proc = HOOKPROC(self._on_native_mouse)
            self._hook = _set_hook(WH_MOUSE_LL, self._hook_proc, None, 0)
            if not self._hook:
                raise OSError(f"Mouse hook installation failed ({ctypes.get_last_error()})")
            self._callback_thread = threading.Thread(
                target=self._dispatch_clicks, name="ClickCancellation", daemon=True
            )
            self._callback_thread.start()
            self._ready.set()
            logger.debug("Started passive mouse event observation")
            while not self._stop_event.is_set():
                # PeekMessage dispatches low-level hooks on their owning thread.
                while _peek_message(ctypes.byref(msg), None, 0, 0, 1):
                    _user32.TranslateMessage(ctypes.byref(msg))
                    _user32.DispatchMessageW(ctypes.byref(msg))
                foreground = _read_foreground()
                if (
                    previous_foreground is not None
                    and foreground
                    and foreground != previous_foreground
                ):
                    position = _read_position()
                    if position is not None:
                        self._clicks.put(position)
                previous_foreground = foreground
                if self._stop_event.wait(self.POLL_INTERVAL):
                    break
        except Exception:
            if not self._ready.is_set():
                self._start_error = "Could not install the mouse monitor"
            logger.exception("Mouse monitor failed")
        finally:
            self._stop_event.set()
            if self._hook:
                _unhook(self._hook)
                self._hook = None
            self._hook_proc = None
            self._ready.set()
            with self._lock:
                self._is_running = False
