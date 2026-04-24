import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Mock the logger and UI bridge before importing UpdateManager
sys.modules["..logging"] = MagicMock()
sys.modules["..ui_utils"] = MagicMock()

from engine.services.updates import UpdateManager, UpdateState  # noqa: E402


def test_sanitize_for_external_process_windows():
    if sys.platform != "win32":
        return

    # Create UpdateManager (mock dependencies)
    manager = UpdateManager(on_update_available=MagicMock(), stop_event=MagicMock())

    # Setup fake _MEIPASS
    fake_mei = "C:\\Temp\\_MEI1234"

    with (
        patch("sys._MEIPASS", fake_mei, create=True),
        patch.dict(
            os.environ,
            {"_MEIPASS": fake_mei, "PATH": f"C:\\Windows;{fake_mei};{fake_mei}\\bin"},
        ),
        patch("ctypes.windll.kernel32.SetDllDirectoryW") as mock_set_dll,
    ):
        clean_env = manager.sanitize_for_external_process()

        # Verify DLL search path was reset
        mock_set_dll.assert_called_once_with(None)

        # Verify _MEIPASS removed from env
        assert "_MEIPASS" not in clean_env

        # Verify PATH scrubbed
        new_path = clean_env.get("PATH", "")
        assert fake_mei not in new_path
        assert "C:\\Windows" in new_path

        # Verify restart flag set
        assert clean_env.get("PYINSTALLER_RESET_ENVIRONMENT") == "1"


def test_sanitize_for_external_process_no_mei():
    # Create UpdateManager
    manager = UpdateManager(on_update_available=MagicMock(), stop_event=MagicMock())

    with (
        patch.dict(os.environ, {"PATH": "C:\\Windows"}),
        patch("sys.platform", "win32"),
        patch("ctypes.windll.kernel32.SetDllDirectoryW") as mock_set_dll,
    ):
        # Ensure _MEIPASS is NOT present
        if hasattr(sys, "_MEIPASS"):
            del sys._MEIPASS

        clean_env = manager.sanitize_for_external_process()

        mock_set_dll.assert_called_once_with(None)
        assert clean_env.get("PATH") == "C:\\Windows"
        assert clean_env.get("PYINSTALLER_RESET_ENVIRONMENT") == "1"


def test_install_now_shell_execute():
    if sys.platform != "win32":
        return

    manager = UpdateManager(on_update_available=MagicMock(), stop_event=MagicMock())
    manager.state = UpdateState.READY_TO_INSTALL
    manager.installer_path = Path("C:\\Temp\\setup.exe")

    with (
        patch("ctypes.windll.shell32.ShellExecuteW") as mock_shell,
        patch.object(manager, "sanitize_for_external_process") as mock_sanitize,
        patch("os.getpid", return_value=1234),
    ):
        mock_shell.return_value = 42  # Success

        result = manager.install_now()

        assert result is True
        mock_sanitize.assert_called_once()
        mock_shell.assert_called_once_with(
            None, "open", "C:\\Temp\\setup.exe", "/SILENT /pid=1234", None, 1
        )
