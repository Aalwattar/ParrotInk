import ctypes
from typing import Literal, Optional

from engine.logging import get_logger
from engine.platform_win.editor_focus import (
    FocusedElement,
    TargetAssessment,
    assess_target,
    read_focused_element,
)
from engine.platform_win.window_focus import (
    GA_ROOT,
    GUITHREADINFO,
    get_ancestor,
    get_foreground_window,
    get_window_thread_process_id,
    user32,
    window_from_point,
)

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
        self.editor: Optional[FocusedElement] = None
        self.focused_element: Optional[FocusedElement] = None

    @property
    def assessment(self) -> TargetAssessment:
        return assess_target(self.focused_element)

    @property
    def can_dictate(self) -> bool:
        return self.assessment.decision == "editable"

    @classmethod
    def capture_current(cls, scope: Literal["control", "window"]) -> "Anchor":
        """Captures the current foreground state as an anchor."""
        anchor = cls(scope)
        anchor.hwnd = get_foreground_window()

        if anchor.hwnd:
            _, anchor.process_id = get_window_thread_process_id(anchor.hwnd)
            focused = read_focused_element()
            if anchor.hwnd != get_foreground_window():
                focused = None
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
                return self.focused_element is None or self._matching_editor() is not None

            # If the foreground window has changed but the root is the same, it's a match
            return False

        elif self.scope == "control":
            if self.editor:
                focused = self._matching_editor(same_editor=True)
                if focused is None:
                    return False
                left, top, right, bottom = focused.bounds
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

    def _matching_editor(self, *, same_editor: bool = False) -> FocusedElement | None:
        focused = read_focused_element() if self.focused_element else None
        if focused is None or not focused.can_dictate:
            return None
        original = self.editor or (self.focused_element if same_editor else None)
        if original is not None and focused.runtime_id != original.runtime_id:
            return None
        return focused

    def has_focus(self, *, same_editor: bool = False) -> bool:
        foreground = get_foreground_window()
        if not foreground or not self.hwnd:
            return False
        if get_ancestor(foreground, GA_ROOT) != get_ancestor(self.hwnd, GA_ROOT):
            return False
        if (self.focused_element or same_editor) and self._matching_editor(
            same_editor=same_editor
        ) is None:
            return False
        if self.editor:
            return True
        return self.scope == "window" or self._get_focused_control(foreground) == self.control_hwnd
