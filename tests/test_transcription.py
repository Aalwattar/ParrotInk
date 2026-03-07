from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.config import Config
from engine.transcription.assemblyai_provider import AssemblyAIProvider


@pytest.fixture
def base_config():
    config = Config()
    config.test.enabled = True
    return config


@pytest.mark.asyncio
async def test_assemblyai_v3_turn_events(base_config):
    """Verify that AssemblyAI Provider correctly processes v3 Real-time turn events."""
    on_partial = MagicMock()
    on_final = MagicMock()

    from engine.config_resolver import EffectiveAssemblyAIConfig

    # Construct manually with required fields
    eff_config = EffectiveAssemblyAIConfig(
        url="wss://test",
        sample_rate=16000,
        encoding="pcm_s16le",
        speech_model="test",
        prompt="",
        language_code="en",
        vad_threshold=0.4,
        confidence_threshold=0.0,
        min_silence_ms=400,
        max_silence_ms=1000,
        inactivity_timeout=None,
        word_boost=None,
        format_text=True,
        language_detection=False,
        stop_timeout=7.0,
        is_test=True,
    )

    provider = AssemblyAIProvider("test_key", on_partial, on_final, eff_config, on_status=None)

    # 1. Simulate Session Start (Turn Start)
    session_start = {"message_type": "SessionBegins", "session_id": "test_id"}
    await provider._handle_event(session_start)

    # 2. Simulate Partial Transcript
    partial = {
        "message_type": "PartialTranscript",
        "text": "hello",
        "audio_start": 0,
        "audio_end": 500,
        "confidence": 0.9,
    }
    await provider._handle_event(partial)
    on_partial.assert_called_with("hello")

    # 3. Simulate Final Transcript (Turn End)
    final = {
        "message_type": "FinalTranscript",
        "text": "hello world",
        "audio_start": 0,
        "audio_end": 1000,
        "confidence": 0.95,
        "punctuated": True,
        "text_formatted": True,
    }
    await provider._handle_event(final)
    on_final.assert_called_with("hello world")


@pytest.mark.asyncio
async def test_assemblyai_provider_send_audio(base_config):
    """Verify that send_audio correctly wraps chunks in the AssemblyAI v3 protocol."""
    with patch("websockets.asyncio.client.connect", new_callable=AsyncMock) as mock_connect:
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws

        from engine.config_resolver import EffectiveAssemblyAIConfig

        eff_config = EffectiveAssemblyAIConfig(
            url="wss://test",
            sample_rate=16000,
            encoding="pcm_s16le",
            speech_model="test",
            prompt="",
            language_code="en",
            vad_threshold=0.4,
            confidence_threshold=0.0,
            min_silence_ms=400,
            max_silence_ms=1000,
            inactivity_timeout=None,
            word_boost=None,
            format_text=True,
            language_detection=False,
            stop_timeout=7.0,
            is_test=True,
        )

        provider = AssemblyAIProvider("test_key", MagicMock(), MagicMock(), eff_config, None)
        await provider.start()

        # Send a silent chunk - protocol is raw bytes for binary contract
        audio_chunk = b"\x00" * 2048
        await provider.send_audio(audio_chunk, 0.0)

        assert mock_ws.send.called
        sent_data = mock_ws.send.call_args[0][0]
        assert isinstance(sent_data, bytes)
