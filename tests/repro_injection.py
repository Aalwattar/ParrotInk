import ctypes
import time
from ctypes import wintypes

# Windows API Constants
USER32 = ctypes.WinDLL("user32", use_last_error=True)
INPUT_KEYBOARD = 1
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP = 0x0002


# 64-bit structures with correct padding
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]

    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", wintypes.DWORD),
        # Padding for 64-bit alignment: the union must start at an 8-byte boundary
        ("padding", wintypes.DWORD),
        ("_input", _INPUT),
    ]


def test_injection():
    print("Injection test starting in 3 seconds...")
    print("PLEASE FOCUS A TEXT EDITOR (like Notepad) NOW.")
    time.sleep(3)

    text = "Hello from SendInput!"
    print(f"Injecting: {text}")

    inputs = []
    for char in text:
        cp = ord(char)
        # Down
        ki_down = KEYBDINPUT(0, cp, KEYEVENTF_UNICODE, 0, 0)
        inputs.append(INPUT(INPUT_KEYBOARD, 0, _INPUT=INPUT._INPUT(ki=ki_down)))
        # Up
        ki_up = KEYBDINPUT(0, cp, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0)
        inputs.append(INPUT(INPUT_KEYBOARD, 0, _INPUT=INPUT._INPUT(ki=ki_up)))

    n_inputs = len(inputs)
    input_array = (INPUT * n_inputs)(*inputs)

    res = USER32.SendInput(n_inputs, ctypes.byref(input_array), ctypes.sizeof(INPUT))
    print(f"SendInput result: {res} (expected {n_inputs})")
    if res != n_inputs:
        print(f"Error code: {ctypes.get_last_error()}")


if __name__ == "__main__":
    test_injection()
