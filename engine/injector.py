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
)

logger = get_logger("Injector")

# Windows API Constants & Structures
USER32 = ctypes.WinDLL("user32", use_last_error=True)


def inject_text(text: str):
    """
    Inject text using Windows SendInput API with Unicode support.
    Handles \r and \n correctly for Windows CRLF newline standards.
    """
    if not text:
        return

    start_time = time.perf_counter()

    inputs = []
    for char in text:
        codepoint = ord(char)

        # KEYEVENTF_UNICODE allows Windows to handle \r and \n naturally
        # as Carriage Return (0x0D) and Line Feed (0x0A) keyboard events.
        ki_down = KEYBDINPUT(0, codepoint, KEYEVENTF_UNICODE, 0, 0)
        inp_down = INPUT()
        inp_down.type = INPUT_KEYBOARD
        inp_down.union.ki = ki_down
        inputs.append(inp_down)

        ki_up = KEYBDINPUT(0, codepoint, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0)
        inp_up = INPUT()
        inp_up.type = INPUT_KEYBOARD
        inp_up.union.ki = ki_up
        inputs.append(inp_up)

    n_inputs = len(inputs)
    input_array = (INPUT * n_inputs)(*inputs)
    res = USER32.SendInput(n_inputs, ctypes.byref(input_array), ctypes.sizeof(INPUT))

    if res == 0:
        logger.error(f"SendInput failed with error code {ctypes.get_last_error()}")

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
    Stateful injection that calculates deltas.
    RESETS on Newlines to ensure multi-line script stability.
    """

    def __init__(self):
        self.last_text = ""

    def reset(self):
        self.last_text = ""

    def inject(self, text: str, is_final: bool = False):
        if text == self.last_text and not is_final:
            return

        # ARCHITECTURE RULE: If the incoming text contains a newline,
        # it's a structural change. Reset the buffer to avoid backspacing across lines.
        if "\n" in text or "\r" in text:
            # Type everything new, then reset so we don't 'diff' against multi-line text.
            inject_text(text)
            if is_final:
                if not text.endswith(" "):
                    inject_text(" ")
                self.last_text = ""
            else:
                self.last_text = text
            return

        # Standard Single-Line Diffing
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
