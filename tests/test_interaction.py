import time
from unittest.mock import MagicMock, patch

from pynput import keyboard

from engine.interaction import InputMonitor


def test_input_monitor_any_key_callback():
    """Verify that any key press triggers the registered callback when enabled."""
    on_press = MagicMock()
    on_release = MagicMock()
    with patch("pynput.keyboard.Listener"):
        monitor = InputMonitor(on_press=on_press, on_release=on_release)

        callback = MagicMock()
        monitor.set_any_key_callback(callback)
        monitor.start()

        # 1. Test Disabled state
        monitor._on_press_hook(keyboard.Key.space)
        time.sleep(0.2)  # Wait for worker thread
        callback.assert_not_called()
        on_press.assert_called_with(keyboard.Key.space)

        # 2. Test Enabled state
        monitor.enable_any_key_monitoring(True)
        monitor._on_press_hook(keyboard.Key.enter)
        time.sleep(0.2)  # Wait for worker thread
        callback.assert_called_once_with(keyboard.Key.enter)
        on_press.assert_called_with(keyboard.Key.enter)

        monitor.stop()


def test_input_monitor_start_stop():
    """Verify that the monitor can be started and stopped."""
    with patch("pynput.keyboard.Listener") as mock_listener_class:
        mock_listener = mock_listener_class.return_value
        on_press = MagicMock()
        on_release = MagicMock()
        monitor = InputMonitor(on_press=on_press, on_release=on_release)

        monitor.start()
        mock_listener_class.assert_called_once()
        assert monitor._listener is not None
        assert monitor._worker_thread is not None

        monitor.stop()
        assert monitor._listener is None
        mock_listener.stop.assert_called_once()
