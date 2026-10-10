import ctypes
from ctypes import wintypes
from typing import Literal, Optional

from engine.logging import get_logger
from engine.platform_win.editor_focus import read_focused_element

logger = get_logger("Anchor")

# --- ctypes Definitions ---
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

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


class Anchor:
    """
    Represents the 'target' context where dictation started.
    """

    def __init__(self, scope: Literal["control", "window"]):
        self.scope = scope
        self.hwnd: Optional[int] = None
        self.process_id: Optional[int] = None

        # For 'control' scope, we might store the specific HWND of the child control
        self.control_hwnd: Optional[int] = None
        self.editor = None
        self.focused_element = None

    @property
    def can_dictate(self) -> bool:
        return bool(self.focused_element and self.focused_element.can_dictate)

    @classmethod
    def capture_current(cls, scope: Literal["control", "window"]) -> "Anchor":
        """Captures the current foreground state as an anchor."""
        anchor = cls(scope)
        anchor.hwnd = get_foreground_window()

        if anchor.hwnd:
            _, anchor.process_id = get_window_thread_process_id(anchor.hwnd)
            focused = read_focused_element()
            anchor.focused_element = focused

            if scope == "control":
                # Get the specific child control that has focus
                anchor.control_hwnd = cls._get_focused_control(anchor.hwnd)
                if focused and focused.can_dictate:
                    left, top, right, bottom = focused.bounds
                    if right > left and bottom > top:
                        anchor.editor = focused

        logger.debug(
            f"Captured anchor: scope={scope}, hwnd={anchor.hwnd}, control={anchor.control_hwnd}"
        )
        return anchor

    @staticmethod
    def _get_focused_control(foreground_hwnd: int) -> int:
        """Attempts to find the specifically focused child control."""
        tid, _ = get_window_thread_process_id(foreground_hwnd)
        gui_info = GUITHREADINFO()
        gui_info.cbSize = ctypes.sizeof(GUITHREADINFO)

        if user32.GetGUIThreadInfo(tid, ctypes.byref(gui_info)):
            if gui_info.hwndFocus:
                return int(gui_info.hwndFocus)

        return foreground_hwnd

    def is_match(self, x: int, y: int) -> bool:
        """
        Determines if a click at (x, y) is 'inside' the anchor.
        """
        target_hwnd = window_from_point(x, y)
        if not target_hwnd:
            return False

        if self.scope == "window":
            # Target HWND must be the same window or a child of it
            # We check the root owner/parent window
            target_root = get_ancestor(target_hwnd, GA_ROOT)

            if self.hwnd is None:
                return False

            anchor_root = get_ancestor(self.hwnd, GA_ROOT)
            if target_root == anchor_root or target_hwnd == anchor_root:
                return True

            # If the foreground window has changed but the root is the same, it's a match
            return False

        elif self.scope == "control":
            if self.editor:
                focused = read_focused_element()
                if focused and (
                    not focused.can_dictate or focused.runtime_id != self.editor.runtime_id
                ):
                    return False
                left, top, right, bottom = (focused or self.editor).bounds
                if not (left <= x < right and top <= y < bottom):
                    return False
            # For control scope, we strictly check if it's the exact same control
            # or if the control hwnd we captured is the same.
            if target_hwnd == self.control_hwnd:
                return True

            # Fallback: if it's a child of the captured control
            parent = user32.GetParent(target_hwnd)
            while parent:
                if parent == self.control_hwnd:
                    return True
                parent = user32.GetParent(parent)

            return False

        return False

    def has_focus(self) -> bool:
        foreground = get_foreground_window()
        if not foreground or not self.hwnd:
            return False
        if get_ancestor(foreground, GA_ROOT) != get_ancestor(self.hwnd, GA_ROOT):
            return False
        focused = read_focused_element() if self.focused_element else None
        if self.focused_element and (focused is None or not focused.can_dictate):
            return False
        if self.editor:
            return bool(
                focused and focused.can_dictate and focused.runtime_id == self.editor.runtime_id
            )
        return self.scope == "window" or self._get_focused_control(foreground) == self.control_hwnd
