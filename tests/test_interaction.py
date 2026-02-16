from unittest.mock import MagicMock, patch

from engine.interaction import InputMonitor


def test_input_monitor_any_key_callback():
    """Verify that any key press triggers the registered callback when enabled."""
    on_press = MagicMock()
    on_release = MagicMock()

    # Mock keyboard library
    with patch("engine.interaction.keyboard"):
        monitor = InputMonitor(on_press=on_press, on_release=on_release)

        callback = MagicMock()
        monitor.set_any_key_callback(callback)
        monitor.set_hotkey("ctrl+space")
        monitor.start()

        # 1. Test Disabled state
        # Simulate a key event
        event = MagicMock()
        event.event_type = "down"
        event.name = "a"
        monitor._any_key_hook(event)

        callback.assert_not_called()

        # 2. Test Enabled state
        monitor.enable_any_key_monitoring(True)
        monitor._any_key_hook(event)
        callback.assert_called_once_with("a")

        monitor.stop()


def test_input_monitor_start_stop():
    """Verify that the monitor can be started and stopped."""
    with patch("engine.interaction.keyboard") as mock_keyboard:
        on_press = MagicMock()
        on_release = MagicMock()
        monitor = InputMonitor(on_press=on_press, on_release=on_release)
        monitor.set_hotkey("ctrl+space")

        monitor.start()
        # Should call hook() for any-key and either add_hotkey or on_press_key
        assert mock_keyboard.hook.called
        assert mock_keyboard.add_hotkey.called or mock_keyboard.on_press_key.called
        assert monitor._is_running is True

        monitor.stop()
        assert monitor._is_running is False
        mock_keyboard.unhook_all.assert_called_once()
