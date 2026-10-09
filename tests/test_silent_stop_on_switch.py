import asyncio
from unittest.mock import AsyncMock

import pytest

from main import AppState


@pytest.mark.asyncio
async def test_silent_stop_on_provider_switch(coordinator, tmp_path):
    """Verify that AppCoordinator performs a silent stop when provider changes mid-session."""
    # 1. Setup active listening state
    coordinator.state = AppState.LISTENING
    coordinator._loop = asyncio.get_running_loop()
    calls = []

    async def finish_recording(*, silent):
        assert silent is True
        calls.append("finish-start")
        await asyncio.sleep(0)
        calls.append("finish-done")
        coordinator.state = AppState.IDLE

    async def stop_provider():
        assert calls == ["finish-start", "finish-done"]
        calls.append("disconnect")

    coordinator.stop_listening = AsyncMock(side_effect=finish_recording)
    coordinator.connection_manager.stop_provider = AsyncMock(side_effect=stop_provider)

    # 2. Trigger a config change that switches provider
    current = coordinator.config.transcription.provider
    target = "assemblyai" if current == "openai" else "openai"
    coordinator.config.update_and_save(
        {"transcription": {"provider": target}},
        path=str(tmp_path / "test_switch.toml"),
        blocking=True,
    )
    await asyncio.wait_for(asyncio.wrap_future(coordinator._configuration_future), timeout=2.0)
    coordinator.stop_listening.assert_awaited_once_with(silent=True)
    coordinator.connection_manager.stop_provider.assert_awaited_once()
    assert calls == ["finish-start", "finish-done", "disconnect"]
    assert coordinator.connection_manager.config.transcription.provider == target
    # Fixture shutdown invokes stop_provider again; restore its real implementation.
    from engine.connection import ConnectionManager

    coordinator.connection_manager.stop_provider = ConnectionManager.stop_provider.__get__(
        coordinator.connection_manager
    )
