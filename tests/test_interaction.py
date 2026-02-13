from unittest.mock import MagicMock, patch

from pynput import keyboard

from engine.interaction import InputMonitor


def test_input_monitor_any_key_callback():
    """Verify that any key press triggers the registered callback when enabled."""
    on_press = MagicMock()
    on_release = MagicMock()
    monitor = InputMonitor(on_press=on_press, on_release=on_release)

    callback = MagicMock()
    monitor.set_any_key_callback(callback)

    # Should not trigger callback if not enabled
    monitor._on_press(keyboard.Key.space)
    callback.assert_not_called()
    on_press.assert_called_with(keyboard.Key.space)

    # Should trigger callback if enabled
    monitor.enable_any_key_monitoring(True)
    monitor._on_press(keyboard.Key.enter)
    assert callback.call_count == 1
    on_press.assert_called_with(keyboard.Key.enter)


def test_input_monitor_start_stop():
    """Verify that the monitor can be started and stopped."""
    with patch("pynput.keyboard.Listener") as mock_listener_class:
        mock_listener = mock_listener_class.return_value
        on_press = MagicMock()
        on_release = MagicMock()
        monitor = InputMonitor(on_press=on_press, on_release=on_release)

        monitor.start()
        mock_listener_class.assert_called_once()
        mock_listener.start.assert_called_once()

        monitor.stop()
        mock_listener.stop.assert_called_once()
