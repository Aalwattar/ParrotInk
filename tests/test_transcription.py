import json
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from engine.config import Config, HotkeysConfig, TranscriptionConfig
from engine.transcription.assemblyai_provider import AssemblyAIProvider
from engine.transcription.factory import TranscriptionFactory
from engine.transcription.openai_provider import OpenAIProvider


@pytest.mark.asyncio
async def test_openai_provider_send_audio():
    on_partial = MagicMock()
    on_final = MagicMock()
    provider = OpenAIProvider(
        api_key="test_key", on_partial=on_partial, on_final=on_final, base_url="ws://localhost:8081"
    )

    with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws

        await provider.start()

        # Create a dummy audio chunk
        audio_chunk = np.zeros(1024, dtype=np.float32)
        await provider.send_audio(audio_chunk)

        # Check if ws.send was called with the correct event type
        assert mock_ws.send.called
        sent_message = json.loads(mock_ws.send.call_args[0][0])
        assert sent_message["type"] == "input_audio_buffer.append"
        assert "audio" in sent_message


@pytest.mark.asyncio
async def test_assemblyai_provider_send_audio():
    on_partial = MagicMock()
    on_final = MagicMock()
    provider = AssemblyAIProvider(
        api_key="test_key", on_partial=on_partial, on_final=on_final, base_url="ws://localhost:8082"
    )

    with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws

        await provider.start()

        audio_chunk = np.zeros(1024, dtype=np.float32)
        await provider.send_audio(audio_chunk)

        assert mock_ws.send.called
        sent_message = json.loads(mock_ws.send.call_args[0][0])
        assert "audio_data" in sent_message


def test_transcription_factory():
    config = Config(
        active_provider="openai",
        openai_api_key="okey",
        assemblyai_api_key="akey",
        hotkeys=HotkeysConfig(hotkey="ctrl+v", hold_mode=True),
        transcription=TranscriptionConfig(language="en", sample_rate=16000),
    )

    on_partial = MagicMock()
    on_final = MagicMock()

    provider = TranscriptionFactory.create(config, on_partial, on_final)
    assert isinstance(provider, OpenAIProvider)

    config.active_provider = "assemblyai"
    provider = TranscriptionFactory.create(config, on_partial, on_final)
    assert isinstance(provider, AssemblyAIProvider)


@pytest.mark.asyncio
async def test_openai_provider_custom_url():
    on_partial = MagicMock()
    on_final = MagicMock()
    custom_url = "ws://my-mock:8000"
    provider = OpenAIProvider(
        api_key="test_key", on_partial=on_partial, on_final=on_final, base_url=custom_url
    )

    assert provider.url == custom_url

    with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws
        await provider.start()
        mock_connect.assert_called_with(custom_url)


@pytest.mark.asyncio
async def test_assemblyai_provider_custom_url():
    on_partial = MagicMock()
    on_final = MagicMock()
    custom_url = "ws://my-mock:9000"
    provider = AssemblyAIProvider(
        api_key="test_key", on_partial=on_partial, on_final=on_final, base_url=custom_url
    )

    assert provider.url == custom_url

    with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws
        await provider.start()
        mock_connect.assert_called_with(custom_url)
