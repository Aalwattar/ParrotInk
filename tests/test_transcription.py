import pytest
import asyncio
import json
import numpy as np
from unittest.mock import AsyncMock, patch, MagicMock
from engine.transcription.openai_provider import OpenAIProvider
from engine.transcription.assemblyai_provider import AssemblyAIProvider
from engine.transcription.factory import TranscriptionFactory
from engine.config import Config, HotkeysConfig, TranscriptionConfig

@pytest.fixture
def base_config():
    return Config()

@pytest.mark.asyncio
async def test_openai_provider_send_audio(base_config):
    on_partial = MagicMock()
    on_final = MagicMock()
    provider = OpenAIProvider(
        api_key="test_key", 
        on_partial=on_partial, 
        on_final=on_final, 
        config=base_config
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
async def test_openai_provider_url_construction(base_config):
    base_config.providers.openai.core.realtime_ws_url_base = "wss://api.openai.com/v1/realtime"
    base_config.providers.openai.core.realtime_ws_model = "gpt-4o-realtime-preview-2024-10-01"
    
    on_partial = MagicMock()
    on_final = MagicMock()
    provider = OpenAIProvider(
        api_key="test_key", 
        on_partial=on_partial, 
        on_final=on_final, 
        config=base_config
    )
    
    expected_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
    assert provider.url == expected_url

@pytest.mark.asyncio
async def test_openai_provider_session_update(base_config):
    base_config.providers.openai.core.transcription_model = "whisper-custom"
    base_config.providers.openai.core.language = "fr"
    base_config.providers.openai.advanced.vad_threshold = 0.8

    on_partial = MagicMock()
    on_final = MagicMock()
    provider = OpenAIProvider(
        api_key="test_key", 
        on_partial=on_partial, 
        on_final=on_final, 
        config=base_config
    )

    with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws
        await provider.start()

        # Find the session.update call
        session_update = None
        for call in mock_ws.send.call_args_list:
            arg = call[0][0]
            if isinstance(arg, str):
                msg = json.loads(arg)
                if msg["type"] == "session.update":
                    session_update = msg
                    break
        
        assert session_update is not None
        session = session_update["session"]
        assert session["input_audio_transcription"]["model"] == "whisper-custom"
        assert session["turn_detection"]["threshold"] == 0.8

@pytest.mark.asyncio
async def test_assemblyai_provider_send_audio(base_config):
    on_partial = MagicMock()
    on_final = MagicMock()
    provider = AssemblyAIProvider(
        api_key="test_key", 
        on_partial=on_partial, 
        on_final=on_final, 
        config=base_config
    )

    with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws

        await provider.start()

        audio_chunk = np.zeros(1024, dtype=np.float32)
        await provider.send_audio(audio_chunk)

        # In V3, it should be bytes, not JSON string
        assert mock_ws.send.called
        sent_data = mock_ws.send.call_args[0][0]
        assert isinstance(sent_data, bytes)

@pytest.mark.asyncio
async def test_assemblyai_provider_v3_url(base_config):
    on_partial = MagicMock()
    on_final = MagicMock()
    provider = AssemblyAIProvider(
        api_key="test_key", 
        on_partial=on_partial, 
        on_final=on_final, 
        config=base_config
    )
    
    # AssemblyAI V3 URL construction
    assert "streaming.assemblyai.com/v3/ws" in provider.url
    assert "sample_rate=16000" in provider.url

def test_transcription_factory(base_config):
    on_partial = MagicMock()
    on_final = MagicMock()

    provider = TranscriptionFactory.create(base_config, on_partial, on_final)
    assert isinstance(provider, OpenAIProvider)

    base_config.default_provider = "assemblyai"
    provider = TranscriptionFactory.create(base_config, on_partial, on_final)
    assert isinstance(provider, AssemblyAIProvider)
