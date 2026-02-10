import time

import win32api
import win32con


def inject_text(text: str):
    """Inject text at the current cursor position using simulated keyboard events."""
    if not text:
        return

    print(f"Injecting text: {text}")

    # We use a slightly more robust approach:
    # 1. Type the characters using SendInput (simulated by keybd_event or similar in win32)
    # 2. For Unicode characters, we might need a different approach,
    # but for basic text, this works well.

    for char in text:
        # Get the virtual key code for the character
        res = win32api.VkKeyScan(char)
        if res == -1:
            # For characters not in the current keyboard layout, we might need to send them as unicode
            # However, for simplicity and speed, we'll focus on standard characters first.
            continue

        vk = res & 0xFF
        shift = (res >> 8) & 0xFF

        if shift & 1:  # Shift key required
            win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)

        win32api.keybd_event(vk, 0, 0, 0)
        win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)

        if shift & 1:
            win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)

        # Small delay to prevent overwhelming the target app
        time.sleep(0.005)


# Alternative robust approach for unicode using SendInput (via ctypes if needed)
# But let's start with this win32api approach and refine if needed.
