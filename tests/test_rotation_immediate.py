import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.app_types import AppState
from engine.config import Config
from main import AppCoordinator


@pytest.mark.asyncio
async def test_immediate_rotation_after_stop():
    """Verify that rotation happens immediately after stop_listening if pending."""
    from engine.audio.adapter import ProviderAudioSpec

    config = Config()
    config.test.enabled = True
    config.audio.connection_mode = "warm"
    config.default_provider = "openai"

    coordinator = AppCoordinator(config)
    coordinator.loop = asyncio.get_running_loop()

    spec = ProviderAudioSpec(sample_rate_hz=24000)

    mock_provider = AsyncMock()
    mock_provider.is_running = True
    mock_provider.get_type = MagicMock(return_value="openai")
    mock_provider.get_audio_spec = MagicMock(return_value=spec)

    coordinator.provider = mock_provider
    coordinator.state = AppState.LISTENING

    # Force rotation pending
    coordinator.connection_manager._rotation_pending = True

    # We expect a new provider to be created
    new_mock = AsyncMock()
    new_mock.is_running = False
    new_mock.get_type = MagicMock(return_value="openai")
    new_mock.get_audio_spec = MagicMock(return_value=spec)

    with patch("engine.transcription.factory.TranscriptionFactory.create", return_value=new_mock):
        # Stop listening should trigger immediate rotation
        await coordinator.stop_listening()

        # Give it a moment for the background task to run
        await asyncio.sleep(0.1)

    # Old provider should have been stopped
    assert mock_provider.stop.called
    # New provider should have been started
    assert new_mock.start.called
    assert coordinator.provider is new_mock
    assert not coordinator.connection_manager._rotation_pending
