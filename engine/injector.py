import time
import ctypes
from ctypes import wintypes
from engine.logging import get_logger

logger = get_logger("Injector")

# Windows API Constants & Structures
USER32 = ctypes.WinDLL('user32', use_last_error=True)

INPUT_KEYBOARD = 1
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP = 0x0002
VK_BACK = 0x08

# Define ULONG_PTR for 64-bit compatibility
IS_64_BIT = ctypes.sizeof(ctypes.c_void_p) == 8
ULONG_PTR = ctypes.c_ulonglong if IS_64_BIT else ctypes.c_ulong

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        # On 64-bit, this union will be padded to start at 8 bytes
        ("union", INPUT_UNION),
    ]

def inject_text(text: str):
    """Inject text efficiently using Windows SendInput API."""
    if not text:
        return

    start_time = time.perf_counter()
    
    inputs = []
    for char in text:
        codepoint = ord(char)
        
        # Key down
        ki_down = KEYBDINPUT(0, codepoint, KEYEVENTF_UNICODE, 0, 0)
        inp_down = INPUT()
        inp_down.type = INPUT_KEYBOARD
        inp_down.union.ki = ki_down
        inputs.append(inp_down)
        
        # Key up
        ki_up = KEYBDINPUT(0, codepoint, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0)
        inp_up = INPUT()
        inp_up.type = INPUT_KEYBOARD
        inp_up.union.ki = ki_up
        inputs.append(inp_up)

    n_inputs = len(inputs)
    input_array = (INPUT * n_inputs)(*inputs)
    
    res = USER32.SendInput(n_inputs, ctypes.byref(input_array), ctypes.sizeof(INPUT))
    
    if res == 0:
        err = ctypes.get_last_error()
        logger.error(f"SendInput failed with error code {err}")
    
    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000
    logger.debug(f"Injection of '{text[:10]}...' took {duration_ms:.2f}ms")

def inject_backspaces(count: int):
    """Inject N backspaces efficiently using Windows SendInput API."""
    if count <= 0:
        return

    start_time = time.perf_counter()
    inputs = []
    for _ in range(count):
        # Backspace Down
        ki_down = KEYBDINPUT(VK_BACK, 0, 0, 0, 0)
        inp_down = INPUT()
        inp_down.type = INPUT_KEYBOARD
        inp_down.union.ki = ki_down
        inputs.append(inp_down)
        
        # Backspace Up
        ki_up = KEYBDINPUT(VK_BACK, 0, KEYEVENTF_KEYUP, 0, 0)
        inp_up = INPUT()
        inp_up.type = INPUT_KEYBOARD
        inp_up.union.ki = ki_up
        inputs.append(inp_up)

    n_inputs = len(inputs)
    input_array = (INPUT * n_inputs)(*inputs)
    
    res = USER32.SendInput(n_inputs, ctypes.byref(input_array), ctypes.sizeof(INPUT))
    if res == 0:
        err = ctypes.get_last_error()
        logger.error(f"SendInput (backspaces) failed with error code {err}")
    
    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000
    logger.debug(f"Backspaces injection completed in {duration_ms:.2f}ms")
