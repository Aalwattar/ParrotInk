import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from engine.app_types import EffectiveOpenAIConfig
from engine.transcription.openai_provider import OpenAIProvider


@pytest.mark.asyncio
async def test_openai_stop_timeout():
    """Verify that OpenAIProvider.stop() does not block indefinitely."""

    config = EffectiveOpenAIConfig(
        transcription_model="gpt-4o-realtime-preview",
        language="en",
        prompt="",
        vad_threshold=0.5,
        turn_detection_type="server_vad",
        prefix_padding_ms=300,
        silence_duration_ms=500,
        url="wss://api.openai.com/v1/realtime",
        noise_reduction_type="off",
        is_test=False,
    )

    provider = OpenAIProvider("fake-key", MagicMock(), MagicMock(), config)

    # Mock Websocket with slow close
    mock_ws = AsyncMock()

    async def slow_close():
        await asyncio.sleep(5.0)

    mock_ws.close.side_effect = slow_close
    provider.ws = mock_ws

    # Ensure receive task is handled
    provider._receive_task = asyncio.create_task(asyncio.sleep(0.1))

    try:
        async with asyncio.timeout(2.5):  # Should finish within 2s (timeout) + overhead
            await provider.stop()
    except TimeoutError:
        pytest.fail("Provider.stop() took longer than 2.5s")

    assert provider.ws is None
    assert not provider.is_running
