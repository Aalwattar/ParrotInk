import asyncio
from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_insertion_guard_runs_after_waiting_for_injection_lock(coordinator, mocker):
    coordinator.loop = asyncio.get_running_loop()
    inject = mocker.patch.object(coordinator.injection_controller.injector, "inject")
    allowed = True
    async with coordinator.injection_controller.lock:
        task = asyncio.create_task(
            coordinator.injection_controller.smart_inject("late text", can_insert=lambda: allowed)
        )
        await asyncio.sleep(0)
        allowed = False
    await task
    inject.assert_not_called()


@pytest.mark.asyncio
async def test_smart_inject_append_only(coordinator):
    coordinator.loop = asyncio.get_running_loop()
    with (
        patch("engine.injector.inject_text") as mock_inject,
        patch("engine.injector.inject_backspaces") as mock_backspace,
    ):
        coordinator.injection_controller.injector.last_text = "Hello"
        await coordinator.injection_controller.smart_inject("Hello world")

        # Give it a tiny bit of time for the executor to run if needed,
        # though run_in_executor with None uses a thread pool that should be fast here.
        await asyncio.sleep(0.1)

        # Should not backspace
        assert not mock_backspace.called
        # Should inject " world"
        mock_inject.assert_called_once_with(" world")
        assert coordinator.injection_controller.injector.last_text == "Hello world"


@pytest.mark.asyncio
async def test_smart_inject_with_backspace(coordinator):
    coordinator.loop = asyncio.get_running_loop()
    with (
        patch("engine.injector.inject_text") as mock_inject,
        patch("engine.injector.inject_backspaces") as mock_backspace,
    ):
        coordinator.injection_controller.injector.last_text = "Hello world"
        await coordinator.injection_controller.smart_inject("Hello there")

        await asyncio.sleep(0.1)

        # Should backspace "world" (5 chars)
        mock_backspace.assert_called_once_with(5)
        # Should inject "there"
        mock_inject.assert_called_once_with("there")
        assert coordinator.injection_controller.injector.last_text == "Hello there"


@pytest.mark.asyncio
async def test_smart_inject_complete_change(coordinator):
    coordinator.loop = asyncio.get_running_loop()
    with (
        patch("engine.injector.inject_text") as mock_inject,
        patch("engine.injector.inject_backspaces") as mock_backspace,
    ):
        coordinator.injection_controller.injector.last_text = "Apple"
        await coordinator.injection_controller.smart_inject("Banana")

        await asyncio.sleep(0.1)

        # Should backspace "Apple" (5 chars)
        mock_backspace.assert_called_once_with(5)
        # Should inject "Banana"
        mock_inject.assert_called_once_with("Banana")
        assert coordinator.injection_controller.injector.last_text == "Banana"
