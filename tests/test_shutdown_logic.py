import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.config import Config
from main import AppCoordinator


@pytest.mark.asyncio
async def test_shutdown_idempotency():
    print("\nStarting test_shutdown_idempotency...")
    config = Config()
    # Mock streamer and UI
    coordinator = AppCoordinator(config)
    coordinator.streamer = MagicMock()
    coordinator.ui_bridge = MagicMock()

    # Mock monitors to avoid real Win32 threads in tests
    coordinator.session_monitor = MagicMock()
    coordinator.input_monitor = MagicMock()
    coordinator.mouse_monitor = MagicMock()

    coordinator.loop = asyncio.get_running_loop()
    print("Coordinator initialized with mocked monitors.")

    # Track calls to stop_provider
    with patch.object(coordinator.connection_manager, "stop_provider", AsyncMock()) as mock_stop:
        print("Triggering parallel shutdowns...")
        # Call shutdown multiple times in parallel
        await asyncio.gather(
            coordinator.shutdown("test1"),
            coordinator.shutdown("test2"),
            coordinator.shutdown("test3"),
        )
        print("Parallel shutdowns complete.")
        # Should only have been called once
        assert mock_stop.call_count == 1
    print("test_shutdown_idempotency finished.")


@pytest.mark.asyncio
async def test_shutdown_deadline_exceeded():
    print("\nStarting test_shutdown_deadline_exceeded...")
    config = Config()
    coordinator = AppCoordinator(config)
    coordinator.streamer = MagicMock()
    coordinator.ui_bridge = MagicMock()

    # Mock monitors
    coordinator.session_monitor = MagicMock()
    coordinator.input_monitor = MagicMock()
    coordinator.mouse_monitor = MagicMock()

    coordinator.loop = asyncio.get_running_loop()
    print("Coordinator initialized.")

    # Mock stop_provider and pipeline.stop to hang
    async def hung_stop(*args, **kwargs):
        print("Simulated hung_stop called, sleeping...")
        await asyncio.sleep(20)

    # Use a mock async context manager that raises TimeoutError on enter
    class MockTimeout:
        async def __aenter__(self):
            print("MockTimeout enter: raising TimeoutError")
            raise asyncio.TimeoutError()

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    with (
        patch.object(coordinator.connection_manager, "stop_provider", hung_stop),
        patch.object(coordinator.pipeline, "stop", hung_stop),
    ):
        # We expect it to call os._exit(1)
        with patch("os._exit") as mock_exit:
            with patch("asyncio.timeout", return_value=MockTimeout()):
                print("Triggering shutdown with timeout...")
                await coordinator.shutdown("test_hang")
                print("Shutdown call finished.")
                assert mock_exit.called
    print("test_shutdown_deadline_exceeded finished.")
