import sys
import winreg
from pathlib import Path

from engine.logging import get_logger

logger = get_logger("Startup")

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "Voice2Text"

def get_executable_path() -> str:
    """Returns the absolute path to the current executable."""
    # sys.executable is usually the right choice for both script and frozen exe
    return str(Path(sys.executable).absolute())

def set_run_at_startup(enabled: bool):
    """
    Creates or deletes the Windows Startup registry value.
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY,
            0,
            winreg.KEY_WRITE
        )
        with key:
            if enabled:
                exe_path = get_executable_path()
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
                logger.info(f"Startup enabled: Registry value set to {exe_path}")
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                    logger.info("Startup disabled: Registry value removed")
                except FileNotFoundError:
                    # Already gone, that's fine
                    pass
    except Exception as e:
        logger.error(f"Failed to set startup registry value: {e}")

def is_run_at_startup_synced() -> bool:
    """
    Checks if the startup registry value exists and matches the current executable path.
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY,
            0,
            winreg.KEY_READ
        )
        with key:
            try:
                value, reg_type = winreg.QueryValueEx(key, APP_NAME)
                if reg_type != winreg.REG_SZ:
                    return False
                
                current_exe = get_executable_path()
                return Path(value).absolute() == Path(current_exe).absolute()
            except FileNotFoundError:
                return False
    except Exception as e:
        logger.error(f"Failed to read startup registry value: {e}")
        return False
