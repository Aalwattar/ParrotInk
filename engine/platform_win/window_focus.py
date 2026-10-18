"""Native focus and physical window ownership shared by accessibility and anchors."""

import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.WindowFromPhysicalPoint.argtypes = [wintypes.POINT]
user32.WindowFromPhysicalPoint.restype = wintypes.HWND
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND
user32.GetParent.argtypes = [wintypes.HWND]
user32.GetParent.restype = wintypes.HWND

# Constants
GA_ROOT = 2


def get_foreground_window() -> int:
    return int(user32.GetForegroundWindow() or 0)


def get_window_thread_process_id(hwnd: int) -> tuple[int, int]:
    """Returns (thread_id, process_id)."""
    pid = wintypes.DWORD()
    tid = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return tid, pid.value


def window_from_point(x: int, y: int) -> int:
    point = wintypes.POINT()
    point.x = x
    point.y = y
    return int(user32.WindowFromPhysicalPoint(point) or 0)


def get_ancestor(hwnd: int, flags: int) -> int:
    return int(user32.GetAncestor(hwnd, flags) or 0)


class GUITHREADINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hwndActive", wintypes.HWND),
        ("hwndFocus", wintypes.HWND),
        ("hwndCapture", wintypes.HWND),
        ("hwndMenuOwner", wintypes.HWND),
        ("hwndMoveSize", wintypes.HWND),
        ("hwndCaret", wintypes.HWND),
        ("rcCaret", wintypes.RECT),
    ]


user32.GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.POINTER(GUITHREADINFO)]
user32.GetGUIThreadInfo.restype = wintypes.BOOL


user32.IsChild.argtypes = [wintypes.HWND, wintypes.HWND]
user32.IsChild.restype = wintypes.BOOL


def native_focus() -> tuple[int, int]:
    foreground = get_foreground_window()
    info = GUITHREADINFO()
    info.cbSize = ctypes.sizeof(info)
    if not foreground or not user32.GetGUIThreadInfo(0, ctypes.byref(info)):
        return 0, 0
    focus = int(info.hwndFocus or 0)
    if not focus or get_ancestor(focus, GA_ROOT) != get_ancestor(foreground, GA_ROOT):
        return 0, 0
    return foreground, focus


def owns_window(focus: int, candidate: int | None) -> bool:
    return bool(candidate and (candidate == focus or user32.IsChild(focus, candidate)))
