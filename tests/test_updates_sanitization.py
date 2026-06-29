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

    # We need to use a real-ish os.environ for this test since we are modifying it in place
    with (
        patch("sys._MEIPASS", fake_mei, create=True),
        patch.dict(
            os.environ,
            {"_MEIPASS": fake_mei, "PATH": f"C:\\Windows;{fake_mei};{fake_mei}\\bin"},
        ),
        patch("ctypes.windll.kernel32.SetDllDirectoryW") as mock_set_dll,
    ):
        manager.sanitize_for_external_process()

        # Verify DLL search path was reset
        mock_set_dll.assert_called_once_with(None)

        # Verify _MEIPASS removed from env
        assert "_MEIPASS" not in os.environ

        # Verify PATH scrubbed
        new_path = os.environ.get("PATH", "")
        assert fake_mei not in new_path
        assert "C:\\Windows" in new_path

        # Verify restart flag set
        assert os.environ.get("PYINSTALLER_RESET_ENVIRONMENT") == "1"


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
        if "_MEIPASS" in os.environ:
            del os.environ["_MEIPASS"]

        manager.sanitize_for_external_process()

        mock_set_dll.assert_called_once_with(None)
        assert os.environ.get("PATH") == "C:\\Windows"
        assert os.environ.get("PYINSTALLER_RESET_ENVIRONMENT") == "1"


def test_install_now_shell_execute():
    if sys.platform != "win32":
        return

    manager = UpdateManager(on_update_available=MagicMock(), stop_event=MagicMock())
    manager.state = UpdateState.READY_TO_INSTALL
    manager.installer_path = Path("C:\\Temp\\setup.exe")

    with (
        patch("ctypes.windll.shell32.ShellExecuteW") as mock_shell,
        patch.object(manager, "sanitize_for_external_process") as mock_sanitize,
        patch.object(manager, "unblock_installer") as mock_unblock,
        patch("os.getpid", return_value=1234),
    ):
        mock_shell.return_value = 42  # Success

        result = manager.install_now()

        assert result is True
        mock_unblock.assert_called_once()
        mock_sanitize.assert_called_once()
        mock_shell.assert_called_once_with(
            None, "open", "C:\\Temp\\setup.exe", "/SILENT /pid=1234", None, 1
        )


def test_unblock_installer_powershell_success():
    manager = UpdateManager(on_update_available=MagicMock(), stop_event=MagicMock())
    manager.installer_path = Path("C:\\Temp\\setup.exe")

    with (
        patch("sys.platform", "win32"),
        patch("engine.services.updates.Path.exists", return_value=True),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)

        result = manager.unblock_installer()

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "Unblock-File" in args[2]


def test_unblock_installer_powershell_fails_python_success():
    manager = UpdateManager(on_update_available=MagicMock(), stop_event=MagicMock())
    manager.installer_path = Path("C:\\Temp\\setup.exe")

    with (
        patch("sys.platform", "win32"),
        patch("engine.services.updates.Path.exists", return_value=True),
        patch("subprocess.run", side_effect=Exception("PowerShell error")),
        patch("os.unlink") as mock_unlink,
    ):
        result = manager.unblock_installer()

        assert result is True
        mock_unlink.assert_called_once_with("C:\\Temp\\setup.exe:Zone.Identifier")


def test_unblock_installer_python_fails():
    manager = UpdateManager(on_update_available=MagicMock(), stop_event=MagicMock())
    manager.installer_path = Path("C:\\Temp\\setup.exe")

    with (
        patch("sys.platform", "win32"),
        patch("engine.services.updates.Path.exists", return_value=True),
        patch("subprocess.run", side_effect=Exception("PowerShell error")),
        patch("os.unlink", side_effect=Exception("Permission error")),
    ):
        result = manager.unblock_installer()

        assert result is False


def test_unblock_installer_not_win32():
    manager = UpdateManager(on_update_available=MagicMock(), stop_event=MagicMock())
    manager.installer_path = Path("C:\\Temp\\setup.exe")

    with (
        patch("sys.platform", "darwin"),
        patch("engine.services.updates.Path.exists", return_value=True),
    ):
        result = manager.unblock_installer()

        assert result is False
