import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock winreg before importing the module under test
mock_winreg = MagicMock()
sys.modules["winreg"] = mock_winreg

from engine.platform_win.startup import is_run_at_startup_synced, set_run_at_startup  # noqa: E402


@pytest.fixture(autouse=True)
def reset_mocks():
    mock_winreg.reset_mock()
    # Setup some default behaviors for winreg
    mock_winreg.HKEY_CURRENT_USER = "HKCU"
    mock_winreg.KEY_WRITE = 1
    mock_winreg.KEY_READ = 2
    mock_winreg.REG_SZ = 3
    # Setup context manager mock
    # OpenKey returns a handle which is also a context manager
    handle = mock_winreg.OpenKey.return_value
    handle.__enter__.return_value = handle
    mock_winreg.QueryValueEx.side_effect = None
    mock_winreg.OpenKey.side_effect = None


def test_set_run_at_startup_enable_script_mode():
    with patch("sys.executable", r"C:\path\to\python.exe"):
        with patch("sys.argv", [r"C:\app\main.py"]):
            with patch("sys.frozen", False, create=True):
                set_run_at_startup(True)

                expected_command = r'"C:\path\to\python.exe" "C:\app\main.py"'
                mock_winreg.SetValueEx.assert_called_once_with(
                    mock_winreg.OpenKey.return_value,
                    "Voice2Text",
                    0,
                    mock_winreg.REG_SZ,
                    expected_command,
                )


def test_set_run_at_startup_enable_frozen():
    with patch("sys.executable", r"C:\path\to\voice2text.exe"):
        with patch("sys.frozen", True, create=True):
            set_run_at_startup(True)

            # Should open the key
            mock_winreg.OpenKey.assert_called_once()
            # Should set the value
            mock_winreg.SetValueEx.assert_called_once_with(
                mock_winreg.OpenKey.return_value,
                "Voice2Text",
                0,
                mock_winreg.REG_SZ,
                r"C:\path\to\voice2text.exe",
            )


def test_set_run_at_startup_disable():
    set_run_at_startup(False)

    # Should open the key
    mock_winreg.OpenKey.assert_called_once()
    # Should delete the value
    mock_winreg.DeleteValue.assert_called_once_with(mock_winreg.OpenKey.return_value, "Voice2Text")


def test_is_run_at_startup_synced_true():
    with patch("sys.executable", r"C:\path\to\voice2text.exe"):
        with patch("sys.frozen", True, create=True):
            mock_winreg.QueryValueEx.return_value = (
                r"C:\path\to\voice2text.exe",
                mock_winreg.REG_SZ,
            )

            assert is_run_at_startup_synced() is True


def test_is_run_at_startup_synced_false_different_path():
    with patch("sys.executable", r"C:\new\path\voice2text.exe"):
        mock_winreg.QueryValueEx.return_value = (r"C:\old\path\voice2text.exe", mock_winreg.REG_SZ)

        assert is_run_at_startup_synced() is False


def test_is_run_at_startup_synced_false_missing_value():
    # FileNotFoundError is raised by QueryValueEx if value doesn't exist
    mock_winreg.QueryValueEx.side_effect = FileNotFoundError

    assert is_run_at_startup_synced() is False


def test_set_run_at_startup_exception():
    mock_winreg.OpenKey.side_effect = Exception("Registry error")
    # Should not raise
    set_run_at_startup(True)
    mock_winreg.OpenKey.assert_called_once()


def test_is_run_at_startup_synced_exception():
    mock_winreg.OpenKey.side_effect = Exception("Registry error")
    # Should not raise
    assert is_run_at_startup_synced() is False
