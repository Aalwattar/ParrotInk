import time

import win32api
import win32con
from engine.logging import get_logger

logger = get_logger("Injector")

def inject_text(text: str):
    """Inject text at the current cursor position using simulated keyboard events."""
    if not text:
        return

    logger.debug(f"Injecting text: {text}")

    for char in text:
        # Unicode support using KEYEVENTF_UNICODE
        # This is more robust than VkKeyScan for non-standard characters
        try:
            # We use 0 as the virtual-key code and the character code as the scan code
            # with the KEYEVENTF_UNICODE flag.
            codepoint = ord(char)
            # KEYEVENTF_UNICODE is 0x0004
            # We send down and up events
            win32api.keybd_event(0, codepoint, win32con.KEYEVENTF_UNICODE, 0)
            win32api.keybd_event(0, codepoint, win32con.KEYEVENTF_UNICODE | win32con.KEYEVENTF_KEYUP, 0)
        except Exception as e:
            logger.error(f"Failed to inject character '{char}': {e}")

        # Small delay to prevent overwhelming the target app
        time.sleep(0.005)