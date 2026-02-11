import asyncio
from unittest.mock import patch

import pytest

from engine.config import Config
from main import AppCoordinator


@pytest.fixture
def coordinator():
    c = Config()
    coord = AppCoordinator(c)
    return coord


@pytest.mark.asyncio
async def test_smart_inject_append_only(coordinator):
    coordinator.loop = asyncio.get_running_loop()
    with (
        patch("main.inject_text") as mock_inject,
        patch("main.inject_backspaces") as mock_backspace,
    ):
        coordinator.last_injected_text = "Hello"
        await coordinator._smart_inject("Hello world")

        # Should not backspace
        assert not mock_backspace.called
        # Should inject " world"
        mock_inject.assert_called_once_with(" world")
        assert coordinator.last_injected_text == "Hello world"


@pytest.mark.asyncio
async def test_smart_inject_with_backspace(coordinator):
    coordinator.loop = asyncio.get_running_loop()
    with (
        patch("main.inject_text") as mock_inject,
        patch("main.inject_backspaces") as mock_backspace,
    ):
        coordinator.last_injected_text = "Hello world"
        await coordinator._smart_inject("Hello there")

        # Should backspace "world" (5 chars)
        mock_backspace.assert_called_once_with(5)
        # Should inject "there"
        mock_inject.assert_called_once_with("there")
        assert coordinator.last_injected_text == "Hello there"


@pytest.mark.asyncio
async def test_smart_inject_complete_change(coordinator):
    coordinator.loop = asyncio.get_running_loop()
    with (
        patch("main.inject_text") as mock_inject,
        patch("main.inject_backspaces") as mock_backspace,
    ):
        coordinator.last_injected_text = "Apple"
        await coordinator._smart_inject("Banana")

        # Should backspace "Apple" (5 chars)
        mock_backspace.assert_called_once_with(5)
        # Should inject "Banana"
        mock_inject.assert_called_once_with("Banana")
        assert coordinator.last_injected_text == "Banana"
