import asyncio
import time
from unittest.mock import MagicMock, patch
import pytest
from pynput import keyboard
from engine.config import Config
from main import AppCoordinator

@pytest.fixture
def config():
    c = Config()
    c.hotkeys.hotkey = "ctrl+alt+v"
    c.hotkeys.hold_mode = True
    return c

@pytest.mark.asyncio
async def test_on_manual_stop_ignores_hotkey_keys(config):
    coordinator = AppCoordinator(config)
    coordinator.loop = asyncio.get_running_loop()
    coordinator.is_listening = True
    coordinator.start_time = time.time() - 1.0 # Past cooldown
    
    # Mock stop_listening
    coordinator.stop_listening = MagicMock(side_effect=coordinator.stop_listening)
    
    # Simulate pressing 'ctrl' (part of hotkey)
    ctrl_key = keyboard.Key.ctrl_l
    coordinator._on_manual_stop(ctrl_key)
    
    # Should NOT have stopped
    assert coordinator.is_listening is True
    assert coordinator.session_cancelled is False

@pytest.mark.asyncio
async def test_on_manual_stop_triggers_on_other_keys(config):
    coordinator = AppCoordinator(config)
    coordinator.loop = asyncio.get_running_loop()
    coordinator.is_listening = True
    coordinator.start_time = time.time() - 1.0
    
    # Mock stop_listening to be a real coroutine that we can wait for
    original_stop = coordinator.stop_listening
    coordinator.stop_listening = MagicMock(side_effect=original_stop)
    
    # Simulate pressing 'space'
    space_key = keyboard.KeyCode.from_char(' ')
    coordinator._on_manual_stop(space_key)
    
    # Give a tiny bit of time for the threadsafe call
    await asyncio.sleep(0.1)
    
    # Should have triggered cancellation
    assert coordinator.session_cancelled is True

@pytest.mark.asyncio
async def test_on_manual_stop_triggers_on_standalone_modifier_not_in_hotkey(config):
    coordinator = AppCoordinator(config)
    coordinator.loop = asyncio.get_running_loop()
    coordinator.is_listening = True
    coordinator.start_time = time.time() - 1.0
    
    # Simulate pressing 'shift' (NOT in ctrl+alt+v)
    shift_key = keyboard.Key.shift_l
    coordinator._on_manual_stop(shift_key)
    
    await asyncio.sleep(0.1)
    
    assert coordinator.session_cancelled is True
