import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from engine.config import Config
from engine.connection import ConnectionManager


async def connect_and_ready(cm: ConnectionManager, is_listening: bool = False):
    """Helper to handle new wait_for_ready synchronization in tests."""
    task = asyncio.create_task(cm.ensure_connected(is_listening=is_listening))
    # Poll for provider initialization to avoid flaky timing
    for _ in range(20):
        if cm.provider:
            break
        await asyncio.sleep(0.05)
    if cm.provider:
        cm.provider._ready_event.set()
    await task


@pytest.mark.asyncio
async def test_ensure_connected_idempotency():
    config = Config()
    config.test.enabled = True
    config.transcription.provider = "openai"

    def set_state(s):
        pass

    cm = ConnectionManager(
        config=config,
        on_partial=lambda x: None,
        on_final=lambda x: None,
        set_state_cb=set_state,
    )

    with patch("websockets.asyncio.client.connect", new_callable=AsyncMock) as mock_connect:
        # Mock successful connection
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws

        # First connection
        await connect_and_ready(cm)
        provider1 = cm.provider
        assert provider1 is not None
        assert provider1.is_running

        # Second connection (should be idempotent)
        await cm.ensure_connected(is_listening=False)
        assert cm.provider is provider1

    await cm.shutdown()


@pytest.mark.asyncio
async def test_openai_rotation_guard():
    config = Config()
    config.test.enabled = True
    config.transcription.provider = "openai"
    config.providers.openai.core.session_rotation_seconds = 1  # Rotate after 1s

    def set_state(s):
        pass

    cm = ConnectionManager(
        config=config,
        on_partial=lambda x: None,
        on_final=lambda x: None,
        set_state_cb=set_state,
    )

    with patch("websockets.asyncio.client.connect", new_callable=AsyncMock) as mock_connect:
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws

        await connect_and_ready(cm)
        provider1 = cm.provider

        # Wait for rotation to be due
        await asyncio.sleep(1.1)

        # ensure_connected while NOT listening should rotate immediately
        await connect_and_ready(cm)
        assert cm.provider is not provider1
        assert cm.provider is not None

    await cm.shutdown()


@pytest.mark.asyncio
async def test_provider_switching():
    config = Config()
    config.test.enabled = True
    config.transcription.provider = "openai"

    def set_state(s):
        pass

    cm = ConnectionManager(
        config=config,
        on_partial=lambda x: None,
        on_final=lambda x: None,
        set_state_cb=set_state,
    )

    with patch("websockets.asyncio.client.connect", new_callable=AsyncMock) as mock_connect:
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws

        await connect_and_ready(cm)
        assert cm.provider.get_type() == "openai"

        # Switch config
        config.transcription.provider = "assemblyai"

        # ensure_connected should switch provider
        await connect_and_ready(cm)
        assert cm.provider.get_type() == "assemblyai"

    await cm.shutdown()
