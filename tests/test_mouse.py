import pytest
from unittest.mock import MagicMock, patch
from engine.mouse import MouseMonitor

def test_mouse_monitor_start_stop(mocker):
    mock_listener = mocker.patch("pynput.mouse.Listener")
    
    monitor = MouseMonitor(on_click_event=lambda x, y: None)
    monitor.start()
    assert monitor._is_running is True
    mock_listener.assert_called_once()
    
    monitor.stop()
    assert monitor._is_running is False
    mock_listener.return_value.stop.assert_called_once()

def test_mouse_monitor_callback(mocker):
    mock_cb = MagicMock()
    monitor = MouseMonitor(on_click_event=mock_cb)
    
    # Simulate pynput callback
    from pynput import mouse
    monitor._on_click(10.5, 20.7, mouse.Button.left, True)
    
    mock_cb.assert_called_once_with(10, 20)
    
    # Right click should not trigger it
    mock_cb.reset_mock()
    monitor._on_click(10.5, 20.7, mouse.Button.right, True)
    mock_cb.assert_not_called()
    
    # Release should not trigger it
    monitor._on_click(10.5, 20.7, mouse.Button.left, False)
    mock_cb.assert_not_called()
