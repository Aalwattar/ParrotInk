import pytest
from unittest.mock import MagicMock, patch
from engine.interaction import InteractionMonitor
from pynput import keyboard

def test_interaction_monitor_any_key_callback():
    """Verify that any key press triggers the registered callback."""
    monitor = InteractionMonitor()
    callback = MagicMock()
    monitor.set_any_key_callback(callback)
    
    # Simulate a key press
    # We'll need to mock the listener or call the internal handler directly
    monitor._on_press(keyboard.Key.space)
    
    callback.assert_called_once()

def test_interaction_monitor_start_stop():
    """Verify that the monitor can be started and stopped."""
    with patch("pynput.keyboard.Listener") as mock_listener_class:
        mock_listener = mock_listener_class.return_value
        monitor = InteractionMonitor()
        
        monitor.start()
        mock_listener_class.assert_called_once()
        mock_listener.start.assert_called_once()
        
        monitor.stop()
        mock_listener.stop.assert_called_once()
