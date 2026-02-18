import os
import sys
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

try:
    from win11toast import toast
except ImportError:
    # Optional dependency: Only required for Windows notifications
    toast = None

if TYPE_CHECKING:
    from .config import Config


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS  # type: ignore
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def get_app_version() -> str:
    """Reads the application version from the project's pyproject.toml file.

    This utility locates the pyproject.toml file in the project root relative to
    the engine directory and extracts the [project].version field.

    Returns:
        str: The version string if found (e.g., "0.2.0"), or "unknown" if the file
             is missing or malformed.
    """
    # Try to find pyproject.toml in the project root
    # engine/ui_utils.py -> parent is engine -> parent is root
    root_path = Path(__file__).parent.parent
    pyproject_path = root_path / "pyproject.toml"

    if not pyproject_path.exists():
        return "unknown"

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            version = data.get("project", {}).get("version", "unknown")
            return str(version)
    except Exception:
        return "unknown"


def show_startup_toast(config: "Config"):
    """Shows a Windows toast notification informing the user ParrotInk is ready.

    Args:
        config (Config): The application configuration, used to get the hotkey.
    """
    if not toast:
        return

    hotkey = config.hotkeys.hotkey.upper()
    try:
        toast(
            title="ParrotInk Ready",
            body=f"Press {hotkey} to start transcription",
            duration="short",
        )
    except Exception:
        # Notifications should be non-blocking and safe to fail
        pass
