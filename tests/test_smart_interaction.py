import asyncio
import pytest
from engine.config import Config, HotkeysConfig, TranscriptionConfig
from main import AppCoordinator
from engine.ui_bridge import UIBridge, UIEvent
from engine.app_types import AppState
from pynput import keyboard

def setup_coordinator():
    config = Config(
        hotkeys=HotkeysConfig(hotkey="ctrl+alt+v", hold_mode=False),
        transcription=TranscriptionConfig(provider="openai"),
    )
    bridge = UIBridge()
    coordinator = AppCoordinator(config, bridge)
    coordinator.test_mode = True # Use test mode to avoid real Win32 calls
    coordinator.loop = asyncio.get_running_loop()
    return coordinator

@pytest.mark.asyncio
async def test_coordinator_uses_input_monitor():
    coordinator = setup_coordinator()
    assert coordinator.input_monitor is not None

@pytest.mark.asyncio
async def test_manual_key_press_stops_listening_and_cancels_injection():
    coordinator = setup_coordinator()
    coordinator.set_state(AppState.LISTENING)
    coordinator.session_cancelled = False
    
    # Simulate a manual key press event from InputMonitor
    # We call the internal handler directly
    coordinator._on_manual_stop(keyboard.Key.esc)
    
    # Give it a moment for the coroutine to run
    await asyncio.sleep(0.1)
    
    assert coordinator.state in (AppState.STOPPING, AppState.IDLE)
    assert coordinator.session_cancelled is True

@pytest.mark.asyncio
async def test_on_final_ignored_if_session_cancelled():
    coordinator = setup_coordinator()
    coordinator.session_cancelled = True
    
    # Track calls to ui_bridge
    calls = []
    def mock_put(ev):
        calls.append(ev)
    
    coordinator.ui_bridge.put_event = mock_put
    
    coordinator.on_final("Hello World")
    
    # Verify no final text event was sent to UI or injection
    final_text_events = [c for c in calls if c[0] == UIEvent.UPDATE_FINAL_TEXT]
    assert len(final_text_events) == 0
