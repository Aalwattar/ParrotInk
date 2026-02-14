import asyncio
import time
from unittest.mock import AsyncMock, patch
import pytest
from engine.config import Config
from engine.connection import ConnectionManager
from engine.app_types import AppState

@pytest.mark.asyncio
async def test_immediate_rotation_after_stop():
    """Verify that rotation happens immediately after stop_listening if pending."""
    config = Config()
    config.test.enabled = True
    config.audio.connection_mode = "warm"
    config.transcription.provider = "openai"
    config.providers.openai.core.session_rotation_seconds = 1  # 1 second for test

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

        # 1. Connect
        await cm.ensure_connected(is_listening=True)
        provider1 = cm.provider
        assert provider1 is not None

        # 2. Wait for session to age
        await asyncio.sleep(1.1)

        # 3. Trigger rotation check while listening
        await cm.ensure_connected(is_listening=True)
        assert cm._rotation_pending is True
        assert cm.provider is provider1

        # 4. Stop listening should trigger immediate rotation
        cm.start_idle_timer()
        
        # Give it a moment to run the async task
        await asyncio.sleep(0.5)
        
        # Verify provider was rotated
        assert cm.provider is not provider1
        assert cm.provider is not None
        assert cm._rotation_pending is False

    await cm.shutdown()
