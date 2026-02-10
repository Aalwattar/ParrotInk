import ctypes
from ctypes import wintypes
import time

# Check Architecture
IS_64_BIT = ctypes.sizeof(ctypes.c_void_p) == 8
print(f"System Architecture: {'64-bit' if IS_64_BIT else '32-bit'}")

# Windows API Constants
USER32 = ctypes.WinDLL('user32', use_last_error=True)
INPUT_KEYBOARD = 1
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP = 0x0002

# Correct Type Definitions
ULONG_PTR = ctypes.c_ulonglong if IS_64_BIT else ctypes.c_ulong

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]
    
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_input", _INPUT),
    ]

def test_injection():
    print(f"Sizeof(INPUT): {ctypes.sizeof(INPUT)}")
    print(f"Sizeof(KEYBDINPUT): {ctypes.sizeof(KEYBDINPUT)}")
    
    # Expected sizes on 64-bit:
    # KEYBDINPUT: 2+2+4+4+(4 pad)+8 = 24 bytes (or possibly 32 if aligned differently)
    # INPUT: 4+(4 pad)+24 = 32 bytes (or 40)
    
    print("Injection test v2 starting in 3 seconds...")
    print("PLEASE FOCUS A TEXT EDITOR (like Notepad) NOW.")
    time.sleep(3)
    
    text = "Hello v2"
    print(f"Injecting: {text}")
    
    inputs = []
    for char in text:
        cp = ord(char)
        # Down
        ki_down = KEYBDINPUT(0, cp, KEYEVENTF_UNICODE, 0, 0)
        inp_down = INPUT()
        inp_down.type = INPUT_KEYBOARD
        inp_down.ki = ki_down
        inputs.append(inp_down)
        
        # Up
        ki_up = KEYBDINPUT(0, cp, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0)
        inp_up = INPUT()
        inp_up.type = INPUT_KEYBOARD
        inp_up.ki = ki_up
        inputs.append(inp_up)

    n_inputs = len(inputs)
    input_array = (INPUT * n_inputs)(*inputs)
    
    print(f"Calling SendInput with n_inputs={n_inputs}, cbSize={ctypes.sizeof(INPUT)}")
    res = USER32.SendInput(n_inputs, ctypes.byref(input_array), ctypes.sizeof(INPUT))
    
    print(f"SendInput result: {res}")
    if res != n_inputs:
        err = ctypes.get_last_error()
        print(f"Error code: {err}")
        # 87 = Invalid Parameter

if __name__ == "__main__":
    test_injection()
