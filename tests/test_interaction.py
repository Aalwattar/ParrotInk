from unittest.mock import MagicMock, patch

from engine.interaction import InteractionMonitor


def test_interaction_monitor_any_key_callback():
    """Verify that any key press triggers the registered callback when enabled."""
    on_press = MagicMock()
    on_release = MagicMock()
    monitor = InteractionMonitor(on_press=on_press, on_release=on_release)

    callback = MagicMock()
    monitor.set_any_key_callback(callback)

    # 1. Test Disabled state
    monitor._on_press("space")
    callback.assert_not_called()

    # 2. Test Enabled state
    monitor.enable_any_key_monitoring(True)
    monitor._on_press("space")
    callback.assert_called_once_with("space")


def test_interaction_monitor_start_stop():
    """Verify that the monitor can be started and stopped."""
    with patch("pynput.keyboard.Listener") as mock_listener:
        on_press = MagicMock()
        on_release = MagicMock()
        monitor = InteractionMonitor(on_press=on_press, on_release=on_release)

        monitor.start()
        mock_listener.assert_called_once()
        assert monitor._listener is not None

        monitor.stop()
        assert monitor._listener is None
