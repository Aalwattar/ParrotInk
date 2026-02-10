import ctypes
from unittest.mock import MagicMock, patch
import pytest
from engine.injector import inject_text

# We need to patch the USER32 object inside engine.injector
@patch("engine.injector.USER32")
def test_inject_text_calls_sendinput(mock_user32):
    # Setup mock
    mock_user32.SendInput.return_value = 2 # 2 inputs for 1 char
    
    inject_text("a")
    
    # Verify SendInput was called
    assert mock_user32.SendInput.called
    args = mock_user32.SendInput.call_args[0]
    # args[0] is nInputs
    assert args[0] == 2 # 1 down, 1 up
    # args[2] is cbSize
    assert args[2] > 0

@patch("engine.injector.USER32")
def test_inject_backspaces_calls_sendinput(mock_user32):
    # This should fail because inject_backspaces is not yet implemented
    from engine.injector import inject_backspaces
    
    mock_user32.SendInput.return_value = 4 # 4 inputs for 2 backspaces
    
    inject_backspaces(2)
    
    assert mock_user32.SendInput.called
    args = mock_user32.SendInput.call_args[0]
    assert args[0] == 4 # 2 down, 2 up
