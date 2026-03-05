import winreg
from typing import Literal


def is_mic_privacy_blocked() -> bool:
    """
    Checks the Windows Registry to see if Microphone access is globally denied
    or denied for Desktop apps.
    """
    try:
        # Check global toggle
        global_path = (
            r"SOFTWARE\Microsoft\Windows\CurrentVersion"
            r"\CapabilityAccessManager\ConsentStore\microphone"
        )
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, global_path) as key:
            val, _ = winreg.QueryValueEx(key, "Value")
            if str(val).lower() == "deny":
                return True

        # Check Desktop Apps toggle (Windows 11 / Recent Win 10)
        desktop_path = (
            r"SOFTWARE\Microsoft\Windows\CurrentVersion"
            r"\CapabilityAccessManager\ConsentStore\microphone\NonPackaged"
        )
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, desktop_path) as key:
            val, _ = winreg.QueryValueEx(key, "Value")
            if str(val).lower() == "deny":
                return True

    except FileNotFoundError:
        pass
    except Exception:
        pass

    return False


def open_settings(page: Literal["microphone", "sound"]):
    """Opens the specific Windows Settings page."""
    uri = "ms-settings:privacy-microphone" if page == "microphone" else "ms-settings:sound"
    try:
        import os

        os.startfile(uri)
    except Exception:
        pass
