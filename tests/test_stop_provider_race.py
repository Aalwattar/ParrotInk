import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from engine.config import Config
from engine.connection import ConnectionManager


@pytest.mark.asyncio
async def test_stop_provider_concurrency_guard():
    """Verify that multiple concurrent stop_provider calls don't race."""
    cfg = Config()
    # Mock callbacks
    cm = ConnectionManager(cfg, MagicMock(), MagicMock(), MagicMock())

    # Mock a provider that takes time to stop
    mock_provider = AsyncMock()

    # We want to simulate a delay to allow another call to enter
    async def delayed_stop():
        await asyncio.sleep(0.1)

    mock_provider.stop = delayed_stop
    mock_provider.is_running = True

    cm.provider = mock_provider
    cm.audio_adapter = MagicMock()

    # Call stop twice concurrently
    # Both tasks will wait for the lock. The first gets it,
    # clears cm.provider, then the second gets it and finds provider is None.
    await asyncio.gather(cm.stop_provider(), cm.stop_provider())

    # If the guard works, provider.stop was called exactly ONCE
    # (assuming delayed_stop is replaced by a spy or similar, but since we
    # replaced provider itself with None, we check if it was called before being set to None)

    # Let's use a counter instead for precise verification
    stop_call_count = 0

    async def counted_stop():
        nonlocal stop_call_count
        stop_call_count += 1
        await asyncio.sleep(0.1)

    mock_provider.stop = counted_stop
    cm.provider = mock_provider

    await asyncio.gather(cm.stop_provider(), cm.stop_provider())

    assert stop_call_count == 1

@pytest.mark.asyncio
async def test_idle_timer_cleans_provider_and_adapter():
    cfg = Config()
    cfg.audio.connection_mode = "warm"
    cm = ConnectionManager(cfg, MagicMock(), MagicMock(), MagicMock())
    provider = MagicMock()
    async def stop():
        await asyncio.sleep(0)

    provider.stop = AsyncMock(side_effect=stop)
    adapter = MagicMock()
    cm.provider, cm.audio_adapter = provider, adapter
    cm._last_activity_time = 0
    cm._idle_timer_task = asyncio.create_task(cm._idle_timer_check())
    await cm._idle_timer_task
    provider.stop.assert_awaited_once()
    adapter.close.assert_called_once()


@pytest.mark.asyncio
async def test_changed_credentials_replace_stopped_provider(mocker):
    cfg = Config()
    cm = ConnectionManager(cfg, MagicMock(), MagicMock(), MagicMock())
    old = MagicMock(is_running=False)
    old.stop = AsyncMock()
    cm.provider = old
    cm.audio_adapter = MagicMock()
    new = MagicMock(is_running=True)
    new.start = AsyncMock()
    new.wait_for_ready = AsyncMock()
    mocker.patch("engine.connection.TranscriptionFactory.create", return_value=new)
    mocker.patch("engine.connection.AudioAdapter")
    cm._credentials_changed = True
    await cm.ensure_connected(is_listening=True)
    assert cm.provider is new
    old.stop.assert_awaited_once()
