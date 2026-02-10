import pytest
import asyncio
from unittest.mock import MagicMock, patch
from main import AppCoordinator
from engine.config import Config, HotkeysConfig, TranscriptionConfig
from engine.interaction import InteractionMonitor

def setup_coordinator():
    config = Config(
        active_provider="openai",
        openai_api_key="test",
        assemblyai_api_key="test",
        hotkeys=HotkeysConfig(hotkey="ctrl+alt+v", hold_mode=False),
        transcription=TranscriptionConfig(sample_rate=16000)
    )
    coordinator = AppCoordinator(config)
    coordinator.loop = asyncio.get_event_loop()
    return coordinator

@pytest.mark.asyncio
async def test_coordinator_uses_interaction_monitor():
    coordinator = setup_coordinator()
    
    # We expect an InteractionMonitor to be created
    assert hasattr(coordinator, "interaction_monitor")
    assert isinstance(coordinator.interaction_monitor, InteractionMonitor)

@pytest.mark.asyncio
async def test_manual_key_press_stops_listening_and_cancels_injection():
    coordinator = setup_coordinator()
    coordinator.provider = MagicMock()
    coordinator.is_listening = True
    
    # Simulate a manual key press via the monitor's callback
    # This should be hooked up in the coordinator
    with patch.object(coordinator, "stop_listening", wraps=coordinator.stop_listening) as mock_stop:
        coordinator.interaction_monitor._on_press(None)
        
        # Wait a bit for the async task if any
        await asyncio.sleep(0.1)
        
        mock_stop.assert_called_once()
        assert coordinator.session_cancelled is True

@pytest.mark.asyncio
async def test_on_final_ignored_if_session_cancelled():
    coordinator = setup_coordinator()
    coordinator.session_cancelled = True
    
    with patch.object(coordinator, "_delayed_inject") as mock_inject:
        coordinator.on_final("Hello")
        await asyncio.sleep(0.1)
        mock_inject.assert_not_called()
