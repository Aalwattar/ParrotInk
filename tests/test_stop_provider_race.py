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
