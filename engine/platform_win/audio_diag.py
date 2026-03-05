import winreg
from typing import Literal


def is_mic_privacy_blocked() -> bool:
    """
    Checks the Windows Registry to see if Microphone access is globally denied
    or denied for Desktop apps (NonPackaged).
    """
    checks = [
        # Global system toggle
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone",
        # Desktop (Win32) app specific toggle
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone\NonPackaged",
    ]
    try:
        for path in checks:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
                val, _ = winreg.QueryValueEx(key, "Value")
                if str(val).lower() == "deny":
                    return True
        return False
    except FileNotFoundError:
        return False  # Key absent = not explicitly blocked
    except Exception:
        return False


def open_settings(page: Literal["microphone", "sound"]):
    """Opens the specific Windows Settings page."""
    uri = "ms-settings:privacy-microphone" if page == "microphone" else "ms-settings:sound"
    try:
        import os

        os.startfile(uri)
    except Exception:
        pass
