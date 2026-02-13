import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.app_types import AppState
from engine.config import Config
from main import AppCoordinator


@pytest.mark.asyncio
async def test_ensure_connected_idempotency():
    config = Config()
    config.test.enabled = True
    config.default_provider = "openai"
    coordinator = AppCoordinator(config)

    mock_provider = MagicMock()
    mock_provider.is_running = True
    mock_provider.get_type.return_value = "openai"
    mock_provider.start = AsyncMock()  # Must be awaitable if called

    coordinator.provider = mock_provider
    coordinator.connection_manager._session_start_time = time.time()

    # Second call should return immediately without calling start()
    await coordinator.ensure_connected()
    assert mock_provider.start.call_count == 0


@pytest.mark.asyncio
async def test_warm_idle_timeout():
    config = Config()
    config.test.enabled = True
    config.audio.connection_mode = "warm"
    config.audio.warm_idle_timeout_seconds = 0.1  # Very short for test

    coordinator = AppCoordinator(config)
    mock_provider = AsyncMock()
    mock_provider.is_running = True
    coordinator.provider = mock_provider
    coordinator.audio_adapter = MagicMock()
    coordinator.state = AppState.LISTENING

    # Stop listening should trigger idle timer
    await coordinator.stop_listening()

    assert coordinator.provider is not None  # Still there (WARM)

    # Wait for timeout
    await asyncio.sleep(0.3)

    # Should have been closed by now
    assert coordinator.provider is None


@pytest.mark.asyncio
async def test_openai_rotation_guard():
    from engine.audio.adapter import ProviderAudioSpec

    config = Config()
    config.test.enabled = True
    config.default_provider = "openai"
    coordinator = AppCoordinator(config)

    spec = ProviderAudioSpec(sample_rate_hz=24000)

    mock_provider = AsyncMock()
    mock_provider.is_running = True
    mock_provider.get_type = MagicMock(return_value="openai")
    mock_provider.get_audio_spec = MagicMock(return_value=spec)
    coordinator.provider = mock_provider
    coordinator.state = AppState.LISTENING

    # Set session start to 1 hour ago
    coordinator.connection_manager._session_start_time = time.time() - 3601

    # 1. ensure_connected should NOT rotate if is_listening is True
    await coordinator.ensure_connected()
    assert coordinator.connection_manager._rotation_pending
    assert coordinator.provider is mock_provider

    # 2. Stop listening should allow rotation on next ensure_connected
    coordinator.state = AppState.IDLE

    # We patch factory create to return a new mock when it tries to reconnect
    new_mock = AsyncMock()
    new_mock.is_running = False  # Initial state
    new_mock.get_type = MagicMock(return_value="openai")
    new_mock.get_audio_spec = MagicMock(return_value=spec)
    with patch("engine.transcription.factory.TranscriptionFactory.create", return_value=new_mock):
        await coordinator.ensure_connected()

    assert mock_provider.stop.called
    assert coordinator.provider is new_mock


@pytest.mark.asyncio
async def test_provider_switching():

    from engine.audio.adapter import ProviderAudioSpec

    config = Config()

    config.test.enabled = True

    config.default_provider = "openai"

    coordinator = AppCoordinator(config)

    spec_openai = ProviderAudioSpec(sample_rate_hz=24000)
    spec_assembly = ProviderAudioSpec(sample_rate_hz=16000)

    mock_openai = AsyncMock()
    mock_openai.is_running = True
    mock_openai.get_type = MagicMock(return_value="openai")
    mock_openai.get_audio_spec = MagicMock(return_value=spec_openai)
    coordinator.provider = mock_openai

    # Switch config to assemblyai
    config.default_provider = "assemblyai"

    # ensure_connected should detect mismatch and stop openai
    new_mock = AsyncMock()
    new_mock.is_running = False
    new_mock.get_type = MagicMock(return_value="assemblyai")
    new_mock.get_audio_spec = MagicMock(return_value=spec_assembly)

    with patch("engine.transcription.factory.TranscriptionFactory.create", return_value=new_mock):
        await coordinator.ensure_connected()

    assert mock_openai.stop.called
    assert coordinator.provider is new_mock
