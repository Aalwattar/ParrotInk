from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from main import AppState


@pytest.mark.asyncio
async def test_silent_stop_on_provider_switch(coordinator):
    """Verify that AppCoordinator performs a silent stop when provider changes mid-session."""
    # 1. Setup active listening state
    coordinator.state = AppState.LISTENING
    coordinator.stop_listening = AsyncMock()
    coordinator._loop = MagicMock()  # Mock loop for run_coroutine_threadsafe

    # 2. Trigger a config change that switches provider
    with patch("asyncio.run_coroutine_threadsafe") as mock_run:
        new_config = coordinator.config
        # Switch from openai to assemblyai (or vice-versa)
        current = coordinator.config.transcription.provider
        target = "assemblyai" if current == "openai" else "openai"
        new_config.transcription.provider = target

        coordinator.config.update_and_save(
            {"transcription": {"provider": target}}, path="test_switch.toml", blocking=True
        )

        # ASSERT: run_coroutine_threadsafe was called with stop_listening(silent=True)
        # We check the arguments of the first call
        assert mock_run.called
        # The first arg is the coroutine object from stop_listening(silent=True)
        # We can verify coordinator.stop_listening was called with silent=True
        coordinator.stop_listening.assert_called_with(silent=True)

    # Cleanup
    import os

    if os.path.exists("test_switch.toml"):
        os.remove("test_switch.toml")
