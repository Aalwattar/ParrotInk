import subprocess
import winreg
from typing import Literal


def is_mic_privacy_blocked() -> bool:
    """
    Checks the Windows Registry to see if Microphone access is globally denied.
    """
    try:
        # Path: HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\
        # CapabilityAccessManager\ConsentStore\microphone
        key_path = (
            r"SOFTWARE\Microsoft\Windows\CurrentVersion"
            r"\CapabilityAccessManager\ConsentStore\microphone"
        )
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            value, _ = winreg.QueryValueEx(key, "Value")
            return str(value).lower() == "deny"
    except FileNotFoundError:
        # If the key doesn't exist, it's usually "Allow" by default or not yet set
        return False
    except Exception:
        return False


def open_settings(page: Literal["microphone", "sound"]):
    """Opens the specific Windows Settings page."""
    uri = "ms-settings:privacy-microphone" if page == "microphone" else "ms-settings:sound"
    try:
        # Use start to handle the URI scheme
        subprocess.Popen(["cmd", "/c", "start", uri], shell=True)
    except Exception:
        pass
