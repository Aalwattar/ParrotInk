import asyncio
import json
from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

import pytest

from engine.config import Config
from engine.connection import ConnectionManager


class ReadyStreamingSocket:
    """A live receiver that acknowledges the current providers' session handshakes."""

    def __init__(self):
        self.events = asyncio.Queue()
        self.events.put_nowait(json.dumps({"type": "Begin", "id": "test-session"}))
        self.close = AsyncMock()
        self.send = AsyncMock(side_effect=self._send)

    async def _send(self, message):
        if isinstance(message, bytes):
            return
        event = json.loads(message)
        if event["type"] == "session.update":
            self.events.put_nowait(json.dumps({"type": "session.updated"}))
        elif event["type"] == "Terminate":
            self.events.put_nowait(json.dumps({"type": "Termination"}))

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self.events.get()


@contextmanager
def mock_streaming_connection():
    with (
        patch.object(Config, "get_openai_key", return_value="test"),
        patch.object(Config, "get_assemblyai_key", return_value="test"),
        patch("websockets.connect", new_callable=AsyncMock) as connect,
    ):
        connect.side_effect = lambda *args, **kwargs: ReadyStreamingSocket()
        yield


async def connect_and_ready(cm: ConnectionManager, is_listening: bool = False):
    """Connect through the actual acknowledgement and persistent receive loop."""
    await asyncio.wait_for(cm.ensure_connected(is_listening=is_listening), timeout=2.0)


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

    with mock_streaming_connection():
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

    with mock_streaming_connection():
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

    with mock_streaming_connection():
        await connect_and_ready(cm)
        assert cm.provider.get_type() == "openai"

        # Switch config
        config.transcription.provider = "assemblyai"

        # ensure_connected should switch provider
        await connect_and_ready(cm)
        assert cm.provider.get_type() == "assemblyai"

    await cm.shutdown()
