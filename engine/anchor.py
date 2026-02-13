import ctypes
from ctypes import wintypes
from typing import Literal, Optional

from engine.logging import get_logger

logger = get_logger("Anchor")

# --- ctypes Definitions ---
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Constants
GA_ROOT = 2


def get_foreground_window() -> int:
    return int(user32.GetForegroundWindow())


def get_window_thread_process_id(hwnd: int) -> tuple[int, int]:
    """Returns (thread_id, process_id)."""
    pid = wintypes.DWORD()
    tid = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return tid, pid.value


def window_from_point(x: int, y: int) -> int:
    point = wintypes.POINT()
    point.x = x
    point.y = y
    return int(user32.WindowFromPoint(point))


def get_ancestor(hwnd: int, flags: int) -> int:
    return int(user32.GetAncestor(hwnd, flags))


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

    @classmethod
    def capture_current(cls, scope: Literal["control", "window"]) -> "Anchor":
        """Captures the current foreground state as an anchor."""
        anchor = cls(scope)
        anchor.hwnd = get_foreground_window()

        if anchor.hwnd:
            _, anchor.process_id = get_window_thread_process_id(anchor.hwnd)

            if scope == "control":
                # Get the specific child control that has focus
                anchor.control_hwnd = cls._get_focused_control(anchor.hwnd)

        logger.debug(
            f"Captured anchor: scope={scope}, hwnd={anchor.hwnd}, control={anchor.control_hwnd}"
        )
        return anchor

    @staticmethod
    def _get_focused_control(foreground_hwnd: int) -> int:
        """Attempts to find the specifically focused child control."""
        # For simplicity and robustness, we can start with the window itself
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
            root_hwnd = get_ancestor(target_hwnd, GA_ROOT)
            return bool(root_hwnd == self.hwnd or target_hwnd == self.hwnd)

        elif self.scope == "control":
            # For control scope, we strictly check if it's the exact same control
            # or if the control hwnd we captured is the same.
            return bool(target_hwnd == self.control_hwnd)

        return False
