from typing import Literal, Optional

import win32gui
import win32process

from engine.logging import get_logger

logger = get_logger("Anchor")


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
        anchor.hwnd = win32gui.GetForegroundWindow()

        if anchor.hwnd:
            _, anchor.process_id = win32process.GetWindowThreadProcessId(anchor.hwnd)

            if scope == "control":
                # Get the specific child control that has focus
                # This is more complex in modern apps, but for legacy/standard apps:
                # GetGUIThreadInfo is the way.
                anchor.control_hwnd = cls._get_focused_control(anchor.hwnd)

        logger.debug(
            f"Captured anchor: scope={scope}, hwnd={anchor.hwnd}, control={anchor.control_hwnd}"
        )
        return anchor

    @staticmethod
    def _get_focused_control(foreground_hwnd: int) -> int:
        """Attempts to find the specifically focused child control."""
        # This uses the Windows API to find the focused element in the foreground window
        # For simplicity and robustness, we can start with the window itself
        # and refine if we have UI Automation libraries.
        # Without a full UIA library, we'll fallback to Window scope
        # but mark the HWND as the anchor.
        return foreground_hwnd

    def is_match(self, x: int, y: int) -> bool:
        """
        Determines if a click at (x, y) is 'inside' the anchor.
        """
        target_hwnd = win32gui.WindowFromPoint((x, y))
        if not target_hwnd:
            return False

        if self.scope == "window":
            # Target HWND must be the same window or a child of it
            # We check the root owner/parent window
            root_hwnd = win32gui.GetAncestor(target_hwnd, 2)  # GA_ROOT = 2
            return bool(root_hwnd == self.hwnd or target_hwnd == self.hwnd)

        elif self.scope == "control":
            # For control scope, we strictly check if it's the exact same control
            # or if the control hwnd we captured is the same.
            return bool(target_hwnd == self.control_hwnd)

        return False
