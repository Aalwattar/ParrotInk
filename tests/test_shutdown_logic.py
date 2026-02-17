import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.config import Config
from main import AppCoordinator


@pytest.mark.asyncio
async def test_shutdown_idempotency():
    config = Config()
    # Mock streamer and UI
    coordinator = AppCoordinator(config)
    coordinator.streamer = MagicMock()
    coordinator.ui_bridge = MagicMock()
    coordinator.loop = asyncio.get_running_loop()

    # Track calls to stop_provider
    with patch.object(coordinator.connection_manager, "stop_provider", AsyncMock()) as mock_stop:
        # Call shutdown multiple times in parallel
        await asyncio.gather(
            coordinator.shutdown("test1"),
            coordinator.shutdown("test2"),
            coordinator.shutdown("test3"),
        )
        # Should only have been called once
        assert mock_stop.call_count == 1


@pytest.mark.asyncio
async def test_shutdown_deadline_exceeded():
    config = Config()
    coordinator = AppCoordinator(config)
    coordinator.streamer = MagicMock()
    coordinator.ui_bridge = MagicMock()
    coordinator.loop = asyncio.get_running_loop()

    # Mock stop_provider and pipeline.stop to hang
    async def hung_stop(*args, **kwargs):
        await asyncio.sleep(20)

    with (
        patch.object(coordinator.connection_manager, "stop_provider", hung_stop),
        patch.object(coordinator.pipeline, "stop", hung_stop),
    ):
        # We expect it to call os._exit(1)
        with patch("os._exit") as mock_exit:
            # Mock asyncio.timeout to raise TimeoutError (from asyncio)
            with patch("asyncio.timeout", side_effect=asyncio.TimeoutError):
                await coordinator.shutdown("test_hang")
                assert mock_exit.called
