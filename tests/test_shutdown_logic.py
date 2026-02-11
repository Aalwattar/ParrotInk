import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from main import AppCoordinator


@pytest.mark.asyncio
async def test_shutdown_idempotency():
    config = MagicMock()
    # Mock streamer and UI
    coordinator = AppCoordinator(config)
    coordinator.streamer = MagicMock()
    coordinator.ui_bridge = MagicMock()
    coordinator.loop = asyncio.get_running_loop()

    # Track calls to stop_listening
    with patch.object(coordinator, "stop_listening", AsyncMock()) as mock_stop:
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
    config = MagicMock()
    coordinator = AppCoordinator(config)
    coordinator.streamer = MagicMock()
    coordinator.ui_bridge = MagicMock()
    coordinator.loop = asyncio.get_running_loop()

    # Mock stop_listening to hang
    async def hung_stop():
        await asyncio.sleep(20)

    with patch.object(coordinator, "stop_listening", hung_stop):
        # We expect it to call os._exit(1)
        with patch("os._exit") as mock_exit:
            # Avoid recursion by using original_timeout
            original_timeout = asyncio.timeout

            def side_effect(t):
                if t == 10.0:
                    return original_timeout(0.1)
                return original_timeout(t)

            with patch("asyncio.timeout", side_effect=side_effect):
                await coordinator.shutdown("test_hang")
                assert mock_exit.called
