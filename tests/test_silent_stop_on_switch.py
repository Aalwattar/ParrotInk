from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from engine.config import Config
from main import AppCoordinator, AppState

@pytest.mark.asyncio
async def test_silent_stop_on_provider_switch():
    """Verify that AppCoordinator triggers a silent stop when provider changes mid-session."""
    cfg = Config()
    cfg.transcription.provider = "openai"
    
    ui_bridge = MagicMock()
    coordinator = AppCoordinator(cfg, ui_bridge)
    coordinator._loop = MagicMock() # Mock loop for run_coroutine_threadsafe
    
    # Force listening state
    coordinator.state = AppState.LISTENING
    
    # Mock stop_listening
    coordinator.stop_listening = AsyncMock()
    
    # Change provider
    with patch("asyncio.run_coroutine_threadsafe") as mock_run:
        # Update config to trigger observer
        cfg.update_and_save({"transcription": {"provider": "assemblyai"}}, blocking=True)
        
        # ASSERT: run_coroutine_threadsafe was called with stop_listening(silent=True)
        # We check the arguments of the first call
        assert mock_run.called
        # The first arg is the coroutine object from stop_listening(silent=True)
        # We can verify coordinator.stop_listening was called with silent=True
        coordinator.stop_listening.assert_called_with(silent=True)
