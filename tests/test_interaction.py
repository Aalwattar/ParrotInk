from unittest.mock import MagicMock, patch

from engine.interaction import Win32InputMonitor


def test_input_monitor_basic_init():
    """Verify that the monitor initializes correctly with callbacks."""
    on_press = MagicMock()
    on_release = MagicMock()
    monitor = Win32InputMonitor(on_press, on_release)

    assert monitor.is_running is False
    assert monitor.hotkey == ""


def test_input_monitor_set_hotkey():
    """Verify hotkey parsing."""
    monitor = Win32InputMonitor(MagicMock(), MagicMock())
    monitor.set_hotkey("ctrl+space")

    assert monitor.hotkey == "ctrl+space"
    # VK_CONTROL = 0x11, Space = 0x20
    assert 0x11 in monitor._modifier_vks
    assert monitor._hotkey_vk == 0x20


def test_input_monitor_start_stop():
    """Verify starting and stopping launches and kills the thread."""
    monitor = Win32InputMonitor(MagicMock(), MagicMock())
    monitor.set_hotkey("ctrl+v")

    # Mock user32.SetWindowsHookExW to avoid actual OS hook in unit test
    with patch("ctypes.windll.user32.SetWindowsHookExW", return_value=123):
        with patch("ctypes.windll.user32.UnhookWindowsHookEx"):
            with patch("ctypes.windll.user32.GetMessageW", return_value=0):  # Exit immediately
                monitor.start()
                assert monitor.is_running is True
                monitor.stop()
                assert monitor.is_running is False
