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
        format_text=True,
        enable_diarization=False,
        stop_timeout=7.0,
        is_test=True,
    )

    provider = AssemblyAIProvider("test_key", on_partial, on_final, eff_config, on_status=None)

    # 1. Simulate Session Start (Turn Start)
    session_start = {"message_type": "SessionBegins", "session_id": "test_id"}
    await provider._handle_event(session_start)

    # 2. Simulate Partial Transcript (Turn)
    partial = {
        "message_type": "Turn",
        "transcript": "hello",
        "end_of_turn": False,
    }
    await provider._handle_event(partial)
    on_partial.assert_called_with("hello")

    # 3. Simulate Final Transcript (Turn End)
    final = {
        "message_type": "Turn",
        "transcript": "hello world",
        "end_of_turn": True,
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
            format_text=True,
            enable_diarization=False,
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


@pytest.mark.asyncio
async def test_assemblyai_diarization_integration(base_config):
    """Verify that SpeakerManager is correctly used when diarization is enabled."""
    on_partial = MagicMock()
    on_final = MagicMock()

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
        format_text=True,
        enable_diarization=True,
        stop_timeout=7.0,
        is_test=True,
    )

    from engine.transcription.speaker_manager import SpeakerManager

    speaker_manager = SpeakerManager()
    provider = AssemblyAIProvider(
        "test_key",
        on_partial,
        on_final,
        eff_config,
        on_status=None,
        speaker_manager=speaker_manager,
    )
    assert provider.speaker_manager is not None

    # Simulate Partial Turn (Should be RAW for HUD)
    event_partial = {
        "message_type": "Turn",
        "transcript": "hello",
        "end_of_turn": False,
        "words": [{"text": "hello", "speaker": 1}],
    }
    await provider._handle_event(event_partial)
    on_partial.assert_called_with("hello")

    # Simulate Final Turn (Should be FORMATTED with Speaker Label)
    event_final = {
        "message_type": "Turn",
        "transcript": "hello",
        "end_of_turn": True,
        "words": [{"text": "hello", "speaker": 1}],
    }
    await provider._handle_event(event_final)
    # SpeakerManager sees has_sent_any_text is false, so no leading \n
    on_final.assert_called_with("[S1] hello")
