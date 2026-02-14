import sys
import winreg
from pathlib import Path

from engine.logging import get_logger

logger = get_logger("Startup")

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "Voice2Text"

def get_executable_path() -> str:
    """
    Returns the command line string to launch the current application.
    Handles both frozen (PyInstaller) and script (Development) modes.
    """
    import sys
    
    # Absolute path to the current executable (python.exe or voice2text.exe)
    exe_path = str(Path(sys.executable).absolute())
    
    if getattr(sys, "frozen", False):
        # Frozen EXE: Just the path to the EXE
        return exe_path
    else:
        # Script Mode: We need [python_path] [script_path]
        # sys.argv[0] is usually the path to main.py
        script_path = str(Path(sys.argv[0]).absolute())
        return f'"{exe_path}" "{script_path}"'

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
                
                current_cmd = get_executable_path()
                # Use simple string comparison for commands which might include quotes
                return value.strip().lower() == current_cmd.strip().lower()
            except FileNotFoundError:
                return False
    except Exception as e:
        logger.error(f"Failed to read startup registry value: {e}")
        return False
