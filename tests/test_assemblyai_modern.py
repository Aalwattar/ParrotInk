import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.app_types import EffectiveAssemblyAIConfig
from engine.transcription.assemblyai_provider import AssemblyAIProvider


@pytest.fixture
def provider():
    config = EffectiveAssemblyAIConfig(
        url="wss://test",
        sample_rate=16000,
        encoding="pcm_s16le",
        speech_model="universal-3-6-pro",
        prompt="",
        language_code="en",
        vad_threshold=0.4,
        confidence_threshold=0.0,
        min_silence_ms=400,
        max_silence_ms=1000,
        inactivity_timeout=None,
        format_text=True,
        enable_diarization=False,
        stop_timeout=0.2,
        is_test=True,
    )
    return AssemblyAIProvider(
        "test-key",
        MagicMock(),
        MagicMock(),
        config,
        on_status=MagicMock(),
        on_error=MagicMock(),
    )


@pytest.mark.asyncio
async def test_begin_controls_readiness_and_records_metadata(provider):
    hold_receive = asyncio.Event()

    async def receive():
        await hold_receive.wait()

    with (
        patch("websockets.asyncio.client.connect", new=AsyncMock(return_value=AsyncMock())),
        patch.object(provider, "_receive_loop", new=receive),
    ):
        await provider.start()
        assert not provider._ready_event.is_set()
        await provider._handle_event(
            {
                "type": "Begin",
                "id": "session-36",
                "expires_at": 123456,
                "configuration": {"model": "universal-3-6-pro"},
            }
        )
        await provider.wait_for_ready(timeout=0.1)
        assert provider.session_id == "session-36"
        assert provider.expires_at == 123456
        assert provider.session_configuration["model"] == "universal-3-6-pro"
        provider._termination_event.set()
        await provider.stop()
        provider.on_error.assert_not_called()


@pytest.mark.asyncio
async def test_formatted_final_revision_is_emitted_once(provider):
    await provider._handle_event(
        {
            "type": "Turn",
            "turn_order": 0,
            "transcript": "hello world",
            "end_of_turn": True,
            "turn_is_formatted": False,
        }
    )
    provider.on_final.assert_not_called()
    formatted = {
        "type": "Turn",
        "turn_order": 0,
        "transcript": "Hello world.",
        "end_of_turn": True,
        "turn_is_formatted": True,
    }
    await provider._handle_event(formatted)
    await provider._handle_event(formatted)
    provider.on_final.assert_called_once_with("Hello world.")
    provider.reset_utterance()
    await provider._handle_event(formatted)
    provider.on_final.assert_called_once_with("Hello world.")


@pytest.mark.asyncio
async def test_finish_flushes_sent_audio_even_without_partial(provider):
    provider.ws = AsyncMock()
    provider._is_running = True
    await provider.send_audio(b"\x01\x00" * 100, 0.0)
    assert not provider.last_transcript

    async def send(message):
        if isinstance(message, str) and json.loads(message)["type"] == "ForceEndpoint":
            await provider._handle_event(
                {
                    "type": "Turn",
                    "turn_order": 0,
                    "transcript": "Short phrase.",
                    "end_of_turn": True,
                    "turn_is_formatted": True,
                }
            )

    provider.ws.send.side_effect = send
    await provider.finish_utterance()
    provider.on_final.assert_called_once_with("Short phrase.")
    provider.ws.close.assert_not_called()
    assert provider.is_running
    sent = [args.args[0] for args in provider.ws.send.call_args_list]
    assert json.dumps({"type": "ForceEndpoint"}) in sent


@pytest.mark.asyncio
async def test_final_empty_turn_unblocks_finish(provider):
    provider.ws = AsyncMock()
    provider._is_running = True
    await provider.send_audio(b"\x00\x00" * 100, 0.0)

    async def send(message):
        await provider._handle_event(
            {
                "type": "Turn",
                "turn_order": 0,
                "transcript": "",
                "end_of_turn": True,
                "turn_is_formatted": True,
            }
        )

    provider.ws.send.side_effect = send
    await provider.finish_utterance()
    assert provider._final_event.is_set()
    assert not provider._pending_audio


@pytest.mark.asyncio
async def test_stop_drains_final_before_termination(provider):
    provider.ws = AsyncMock()
    ws = provider.ws
    provider._is_running = True

    async def send(message):
        if json.loads(message)["type"] == "Terminate":
            await provider._handle_event(
                {
                    "type": "Turn",
                    "turn_order": 0,
                    "transcript": "Last phrase.",
                    "end_of_turn": True,
                    "turn_is_formatted": True,
                }
            )
            await provider._handle_event({"type": "Termination"})

    ws.send.side_effect = send
    await provider.stop()
    provider.on_final.assert_called_once_with("Last phrase.")
    provider.on_error.assert_not_called()
    ws.close.assert_awaited_once()
    assert not provider.is_running


@pytest.mark.asyncio
async def test_receive_loop_eof_reports_failure(provider):
    provider.ws = AsyncMock()
    provider._is_running = True
    provider._ready_event.set()
    await provider._receive_loop()
    assert not provider.is_running
    assert not provider._ready_event.is_set()
    provider.on_error.assert_called_once()


@pytest.mark.asyncio
async def test_finish_timeout_is_bounded(provider):
    provider.ws = AsyncMock()
    provider._is_running = True
    await provider.send_audio(b"\x01\x00" * 100, 0.0)
    with pytest.raises(TimeoutError, match="did not finalize"):
        await asyncio.wait_for(provider.finish_utterance(), timeout=0.5)
    assert provider.is_running


@pytest.mark.asyncio
async def test_finish_transport_loss_cannot_look_like_final_success(provider):
    provider.ws = AsyncMock()
    provider._is_running = True
    await provider.send_audio(b"\x01\x00" * 100, 0.0)

    async def send(message):
        provider._connection_failed("Connection lost before final turn")

    provider.ws.send.side_effect = send
    with pytest.raises(ConnectionError, match="before the current phrase"):
        await provider.finish_utterance()
    provider.on_final.assert_not_called()
    assert not provider.is_running


@pytest.mark.asyncio
async def test_stop_closes_transport_after_pending_final_timeout(provider):
    provider.ws = AsyncMock()
    ws = provider.ws
    provider._is_running = True
    await provider.send_audio(b"\x01\x00" * 100, 0.0)
    await provider.stop()
    ws.close.assert_awaited_once()
    assert provider.ws is None
    assert not provider.is_running
    provider.on_error.assert_not_called()


@pytest.mark.asyncio
async def test_send_failure_reports_once(provider):
    provider.ws = AsyncMock()
    provider.ws.send.side_effect = OSError("network unavailable")
    provider._is_running = True
    await provider.send_audio(b"\x01\x00", 0.0)
    await provider.send_audio(b"\x01\x00", 0.0)
    assert not provider.is_running
    provider.on_error.assert_called_once()
