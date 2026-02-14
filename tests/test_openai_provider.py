import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.config import Config
from engine.config_resolver import resolve_effective_config
from engine.transcription.openai_provider import OpenAIProvider


@pytest.mark.asyncio
async def test_openai_dialect_b_payload():
    """Verify that OpenAIProvider sends the correct Dialect B session update payload."""
    config = Config()
    eff = resolve_effective_config(config)

    on_partial = MagicMock()
    on_final = MagicMock()

    provider = OpenAIProvider(
        api_key="test_key", on_partial=on_partial, on_final=on_final, effective_config=eff.openai
    )

    with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws

        # Start calls _update_session internally
        await provider.start()

        # Check that the first message sent was the session update
        assert mock_ws.send.called
        sent_payload = json.loads(mock_ws.send.call_args_list[0][0][0])

        # Validate Dialect B Schema (Flat)
        assert sent_payload["type"] == "transcription_session.update"
        assert "session" not in sent_payload  # No wrapper
        assert sent_payload["input_audio_format"] == "pcm16"
        assert sent_payload["input_audio_transcription"]["model"] == "gpt-4o-mini-transcribe"
        assert "turn_detection" in sent_payload
        assert sent_payload["input_audio_noise_reduction"]["type"] in [
            "near_field",
            "far_field",
            "off",
        ]


@pytest.mark.asyncio
async def test_openai_dialect_b_events():
    """Verify that OpenAIProvider correctly handles Dialect B events."""
    config = Config()
    eff = resolve_effective_config(config)

    on_partial = MagicMock()
    on_final = MagicMock()

    provider = OpenAIProvider(
        api_key="test_key", on_partial=on_partial, on_final=on_final, effective_config=eff.openai
    )

    # Test Delta Event
    delta_event = {"type": "input_audio_transcription.delta", "delta": "hello"}
    await provider._handle_event(delta_event)
    on_partial.assert_called_with("hello")

    # Test Completed Event
    completed_event = {"type": "input_audio_transcription.completed", "transcript": "hello world"}
    await provider._handle_event(completed_event)
    on_final.assert_called_with("hello world")
