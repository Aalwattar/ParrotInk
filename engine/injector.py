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

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [("type", wintypes.DWORD), ("_input", _INPUT)]

def inject_text(text: str):
    """Inject text efficiently using Windows SendInput API."""
    if not text:
        return

    start_time = time.perf_counter()
    logger.debug(f"Injection started: {text[:20]}...")

    # For each character, we need a down and an up event
    inputs = []
    for char in text:
        codepoint = ord(char)
        
        # Key down
        ki_down = KEYBDINPUT(0, codepoint, KEYEVENTF_UNICODE, 0, None)
        inputs.append(INPUT(INPUT_KEYBOARD, _INPUT=INPUT._INPUT(ki=ki_down)))
        
        # Key up
        ki_up = KEYBDINPUT(0, codepoint, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, None)
        inputs.append(INPUT(INPUT_KEYBOARD, _INPUT=INPUT._INPUT(ki=ki_up)))

    # Convert list to ctypes array
    n_inputs = len(inputs)
    input_array = (INPUT * n_inputs)(*inputs)
    
    # Send all inputs in a single batch
    USER32.SendInput(n_inputs, ctypes.byref(input_array), ctypes.sizeof(INPUT))
    
    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000
    logger.debug(f"Injection completed in {duration_ms:.2f}ms")
