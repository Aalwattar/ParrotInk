import ctypes
import time
from ctypes import wintypes

# Windows API Constants
USER32 = ctypes.WinDLL("user32", use_last_error=True)
INPUT_KEYBOARD = 1
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP = 0x0002

# Type Definitions for 64-bit Windows
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
        ("union", INPUT_UNION),
    ]


def test_injection():
    print(f"System: {'64-bit' if IS_64_BIT else '32-bit'}")
    print(f"Sizeof(INPUT): {ctypes.sizeof(INPUT)}")

    print("\nInjection test starting in 3 seconds...")
    print("PLEASE FOCUS A TEXT EDITOR (like Notepad) NOW.")
    time.sleep(3)

    text = "Hello 64-bit!"
    inputs = []
    for char in text:
        cp = ord(char)
        # Down
        i_down = INPUT()
        i_down.type = INPUT_KEYBOARD
        i_down.union.ki = KEYBDINPUT(0, cp, KEYEVENTF_UNICODE, 0, 0)
        inputs.append(i_down)
        # Up
        i_up = INPUT()
        i_up.type = INPUT_KEYBOARD
        i_up.union.ki = KEYBDINPUT(0, cp, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0)
        inputs.append(i_up)

    n_inputs = len(inputs)
    input_array = (INPUT * n_inputs)(*inputs)

    res = USER32.SendInput(n_inputs, ctypes.byref(input_array), ctypes.sizeof(INPUT))
    print(f"SendInput result: {res} (expected {n_inputs})")
    if res == 0:
        print(f"Error code: {ctypes.get_last_error()}")


if __name__ == "__main__":
    test_injection()
