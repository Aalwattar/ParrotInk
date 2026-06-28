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


def test_assemblyai_universal_35_config_resolution():
    """Verify that universal-3-5-pro resolves its new parameters,
    maps latency_profile, and auto-maps voice_focus.
    """
    from engine.config_resolver import resolve_effective_config

    # Case A: Auto-mapping mic_profile -> voice_focus,
    # language_detection is omitted, defaults populated
    config = Config()
    config.transcription.provider = "assemblyai"
    config.transcription.mic_profile = "headset"
    config.transcription.latency_profile = "balanced"
    config.providers.assemblyai.core.speech_model = "universal-3-5-pro"
    config.providers.assemblyai.core.agent_context = "test greeting"

    eff = resolve_effective_config(config)
    assert eff.assemblyai.speech_model == "universal-3-5-pro"
    assert eff.assemblyai.mode == "balanced"
    assert eff.assemblyai.agent_context == "test greeting"
    assert eff.assemblyai.voice_focus == "near_field"
    assert "mode=balanced" in eff.assemblyai.url
    assert "agent_context=test+greeting" in eff.assemblyai.url
    assert "voice_focus=near_field" in eff.assemblyai.url
    # Ensure language_detection flag is omitted
    assert "language_detection" not in eff.assemblyai.url

    # Case B: Mic profile 'laptop' maps to 'far_field'
    config.transcription.mic_profile = "laptop"
    eff = resolve_effective_config(config)
    assert eff.assemblyai.voice_focus == "far_field"
    assert "voice_focus=far_field" in eff.assemblyai.url

    # Case C: Dynamic mapping of latency_profile -> mode when override is false
    config.transcription.latency_profile = "fast"
    eff = resolve_effective_config(config)
    assert eff.assemblyai.mode == "min_latency"
    assert "mode=min_latency" in eff.assemblyai.url

    config.transcription.latency_profile = "accurate"
    eff = resolve_effective_config(config)
    assert eff.assemblyai.mode == "max_accuracy"
    assert "mode=max_accuracy" in eff.assemblyai.url

    # Case D: When override is true, use core.mode regardless of latency_profile
    config.providers.assemblyai.advanced.override = True
    config.providers.assemblyai.core.mode = "max_accuracy"
    config.transcription.latency_profile = "fast"
    eff = resolve_effective_config(config)
    assert eff.assemblyai.mode == "max_accuracy"
    assert "mode=max_accuracy" in eff.assemblyai.url

    # Case E: Legacy models do not append the new parameters
    config.providers.assemblyai.advanced.override = False
    config.providers.assemblyai.core.speech_model = "universal-streaming-english"
    eff = resolve_effective_config(config)
    assert "mode=" not in eff.assemblyai.url
    assert "agent_context=" not in eff.assemblyai.url
    assert "voice_focus=" not in eff.assemblyai.url


@pytest.mark.asyncio
async def test_assemblyai_provider_update_agent_context():
    """Verify that update_agent_context sends the correct UpdateConfiguration message."""
    from engine.config_resolver import EffectiveAssemblyAIConfig

    eff_config = EffectiveAssemblyAIConfig(
        url="wss://test",
        sample_rate=16000,
        encoding="pcm_s16le",
        speech_model="universal-3-5-pro",
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
        mode="balanced",
        agent_context="",
        voice_focus=None,
    )

    with patch("websockets.asyncio.client.connect", new_callable=AsyncMock) as mock_connect:
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws

        provider = AssemblyAIProvider("test_key", MagicMock(), MagicMock(), eff_config, None)
        await provider.start()

        # Update context mid-stream
        await provider.update_agent_context("Hello user, how are you?")
        assert mock_ws.send.called

        # Extract sent message
        import json

        sent_payload = json.loads(mock_ws.send.call_args[0][0])
        assert sent_payload["type"] == "UpdateConfiguration"
        assert sent_payload["agent_context"] == "Hello user, how are you?"


def test_ui_menu_get_active_model_name():
    """Verify that get_active_model_name extracts the correct active model from TrayApp."""
    from unittest.mock import MagicMock

    from engine.config import Config
    from engine.ui_menu import get_active_model_name

    app = MagicMock()
    app.config = Config()

    # Case A: OpenAI provider
    app.current_provider = "openai"
    app.config.providers.openai.core.transcription_model = "gpt-4o-mini-transcribe"
    assert get_active_model_name(app) == "gpt-4o-mini-transcribe"

    # Case B: AssemblyAI provider
    app.current_provider = "assemblyai"
    app.config.providers.assemblyai.core.speech_model = "universal-3-5-pro"
    assert get_active_model_name(app) == "universal-3-5-pro"

    # Case C: Unknown provider
    app.current_provider = "other"
    assert get_active_model_name(app) == "Unknown"
