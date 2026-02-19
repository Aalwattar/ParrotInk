import ctypes
import threading
from ctypes import wintypes
from typing import Callable, Optional

from engine.logging import get_logger

logger = get_logger("SessionMonitor")

# Win32 Constants for Session Monitoring
NOTIFY_FOR_THIS_SESSION = 0
WM_WTSSESSION_CHANGE = 0x02B1
WTS_SESSION_LOCK = 0x7
WTS_SESSION_UNLOCK = 0x8

# Windows Library Loading
user32 = ctypes.windll.user32
wtsapi32 = ctypes.windll.wtsapi32
kernel32 = ctypes.windll.kernel32

class SessionMonitor:
    """
    Listens for Windows session events (Lock/Unlock) via a hidden window.
    This allows us to re-hook the keyboard immediately after a desktop switch.
    """
    def __init__(self, on_unlock: Callable[[], None]):
        self.on_unlock = on_unlock
        self._thread: Optional[threading.Thread] = None
        self._hwnd: Optional[wintypes.HWND] = None
        self._stop_event = threading.Event()
        self._thread_id: Optional[int] = None

    def start(self):
        """Starts the session monitoring in a dedicated background thread."""
        if self._thread and self._thread.is_alive():
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="SessionMonitorThread", daemon=False)
        self._thread.start()
        logger.debug("SessionMonitor thread started.")

    def _run(self):
        """Hidden window message loop for session notifications."""
        self._thread_id = kernel32.GetCurrentThreadId()

        # Define the Window Class
        WNDPROC = ctypes.WINFUNCTYPE(wintypes.LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

        def wnd_proc(hwnd, msg, wparam, lparam):
            if msg == WM_WTSSESSION_CHANGE:
                if wparam == WTS_SESSION_LOCK:
                    logger.info("Windows Session Locked.")
                elif wparam == WTS_SESSION_UNLOCK:
                    logger.info("Windows Session Unlocked. Triggering hook refresh.")
                    self.on_unlock()
            elif msg == 0x0012: # WM_QUIT
                return 0
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        self._wnd_proc_ptr = WNDPROC(wnd_proc) # Keep reference alive

        class WNDCLASSW(ctypes.Structure):
            _fields_ = [
                ("style", wintypes.UINT),
                ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HCURSOR),
                ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR),
            ]

        class_name = u"ParrotInkSessionMonitor"
        wc = WNDCLASSW()
        wc.lpfnWndProc = self._wnd_proc_ptr
        wc.lpszClassName = class_name
        wc.hInstance = kernel32.GetModuleHandleW(None)

        user32.RegisterClassW(ctypes.byref(wc))

        # Create Hidden Message-Only Window
        self._hwnd = user32.CreateWindowExW(
            0, class_name, u"SessionMonitor",
            0, 0, 0, 0, 0,
            -3, # HWND_MESSAGE
            None, wc.hInstance, None
        )

        if not self._hwnd:
            logger.error("Failed to create SessionMonitor window.")
            return

        # Register for session notifications
        wtsapi32.WTSRegisterSessionNotification(self._hwnd, NOTIFY_FOR_THIS_SESSION)

        # Standard Message Loop
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        # Cleanup on exit
        wtsapi32.WTSUnRegisterSessionNotification(self._hwnd)
        user32.DestroyWindow(self._hwnd)
        user32.UnregisterClassW(class_name, wc.hInstance)
        logger.debug("SessionMonitor thread exited cleanly.")

    def stop(self):
        """Gracefully shuts down the monitoring thread."""
        if self._thread_id:
            logger.debug("Stopping SessionMonitor...")
            user32.PostThreadMessageW(self._thread_id, 0x0012, 0, 0) # WM_QUIT
            if self._thread:
                self._thread.join(timeout=2.0)
            self._thread_id = None
