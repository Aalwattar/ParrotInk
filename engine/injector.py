import ctypes
import time

from engine.logging import get_logger
from engine.platform_win.constants import BACKSPACE_SAFETY_CAP

from .platform_win.keys import (
    INPUT,
    INPUT_KEYBOARD,
    KEYBDINPUT,
    KEYEVENTF_KEYUP,
    KEYEVENTF_UNICODE,
    VK_BACK,
    VK_RETURN,
)

logger = get_logger("Injector")

# Windows API Constants & Structures
USER32 = ctypes.WinDLL("user32", use_last_error=True)


def inject_text(text: str):
    """
    Inject text using Windows SendInput API.
    Converts \n into a physical VK_RETURN (Enter key) press.
    """
    if not text:
        return

    start_time = time.perf_counter()

    inputs = []
    for char in text:
        if char == "\n":
            # PHYSICAL ENTER: Use VK_RETURN for maximum compatibility.
            ki_down = KEYBDINPUT(VK_RETURN, 0, 0, 0, 0)
            ki_up = KEYBDINPUT(VK_RETURN, 0, KEYEVENTF_KEYUP, 0, 0)
        elif char == "\r":
            continue
        else:
            # Standard Unicode injection
            codepoint = ord(char)
            ki_down = KEYBDINPUT(0, codepoint, KEYEVENTF_UNICODE, 0, 0)
            ki_up = KEYBDINPUT(0, codepoint, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0)

        # Build structures
        inp_down = INPUT()
        inp_down.type = INPUT_KEYBOARD
        inp_down.union.ki = ki_down
        inputs.append(inp_down)

        inp_up = INPUT()
        inp_up.type = INPUT_KEYBOARD
        inp_up.union.ki = ki_up
        inputs.append(inp_up)

    if not inputs:
        return

    n_inputs = len(inputs)
    input_array = (INPUT * n_inputs)(*inputs)
    USER32.SendInput(n_inputs, ctypes.byref(input_array), ctypes.sizeof(INPUT))

    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.debug(f"Injection of '{text[:10]}...' took {duration_ms:.2f}ms")


def inject_backspaces(count: int):
    """Inject N physical backspaces."""
    if count <= 0:
        return

    inputs = []
    for _ in range(count):
        ki_down = KEYBDINPUT(VK_BACK, 0, 0, 0, 0)
        inp_down = INPUT()
        inp_down.type = INPUT_KEYBOARD
        inp_down.union.ki = ki_down
        inputs.append(inp_down)

        ki_up = KEYBDINPUT(VK_BACK, 0, KEYEVENTF_KEYUP, 0, 0)
        inp_up = INPUT()
        inp_up.type = INPUT_KEYBOARD
        inp_up.union.ki = ki_up
        inputs.append(inp_up)

    n_inputs = len(inputs)
    input_array = (INPUT * n_inputs)(*inputs)
    USER32.SendInput(n_inputs, ctypes.byref(input_array), ctypes.sizeof(INPUT))


class SmartInjector:
    """
    Handles stateful text injection.
    RESETS on Newlines to prevent backspacing across lines.
    """

    def __init__(self):
        self.last_text = ""

    def reset(self):
        self.last_text = ""

    def inject(self, text: str, is_final: bool = False):
        if text == self.last_text and not is_final:
            return

        # If we see a newline, it's a structural turn change.
        # We inject everything new and reset the diff buffer.
        if "\n" in text or "\r" in text:
            inject_text(text)
            if is_final:
                if not text.endswith(" "):
                    inject_text(" ")
                self.last_text = ""
            else:
                self.last_text = text
            return

        # Standard single-line diffing
        common_len = 0
        for i in range(min(len(self.last_text), len(text))):
            if self.last_text[i] == text[i]:
                common_len += 1
            else:
                break

        backspaces = len(self.last_text) - common_len
        new_text = text[common_len:]

        if backspaces > 0:
            inject_backspaces(min(backspaces, BACKSPACE_SAFETY_CAP))

        if new_text:
            inject_text(new_text)

        if is_final:
            if not text.endswith(" "):
                inject_text(" ")
            self.last_text = ""
        else:
            self.last_text = text
