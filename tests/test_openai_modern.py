import asyncio
import base64
import json
from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.app_types import EffectiveOpenAIConfig
from engine.transcription.openai_provider import OpenAIProvider


def provider(model="gpt-live-transcribe", **overrides):
    cfg = EffectiveOpenAIConfig(
        url="wss://api.openai.com/v1/realtime?intent=transcription",
        transcription_model=model,
        prompt="context",
        turn_detection_type="server_vad",
        vad_threshold=0.5,
        silence_duration_ms=300,
        prefix_padding_ms=300,
        noise_reduction_type="near_field",
        language="en",
        stop_timeout=0.2,
        is_test=False,
    )
    cfg = replace(cfg, **overrides)
    p = OpenAIProvider("secret", MagicMock(), MagicMock(), cfg, on_error=MagicMock())
    p.ws = AsyncMock()
    p._is_running = True
    return p


def messages(p):
    return [json.loads(call.args[0]) for call in p.ws.send.call_args_list]


@pytest.mark.asyncio
@pytest.mark.parametrize("model", ["gpt-live-transcribe", "gpt-transcribe"])
async def test_modern_session_has_manual_turns_and_multiple_languages(model):
    p = provider(model, languages=("en", "fr"), keywords=("ParrotInk",), delay="low")
    await p._update_session()
    config = messages(p)[0]["session"]["audio"]["input"]
    assert config["turn_detection"] is None
    assert config["transcription"]["languages"] == ["en", "fr"]
    assert "language" not in config["transcription"]
    assert config["transcription"]["keywords"] == ["ParrotInk"]
    assert config["transcription"]["delay"] == "low"
    assert config["format"] == {"type": "audio/pcm", "rate": 24000}


@pytest.mark.asyncio
async def test_legacy_session_retains_server_vad():
    p = provider("gpt-4o-mini-transcribe")
    await p._update_session()
    config = messages(p)[0]["session"]["audio"]["input"]
    assert config["turn_detection"]["type"] == "server_vad"
    assert config["transcription"]["language"] == "en"
    assert "languages" not in config["transcription"]


@pytest.mark.asyncio
async def test_silence_commits_once_and_idle_audio_is_skipped():
    p = provider()
    chunk = base64.b64encode(bytes(2400)).decode()
    for active, capture_time in [
        (False, 0.0),
        (True, 0.05),
        (False, 0.1),
        (False, 0.2),
        (False, 0.35),
        (False, 0.4),
    ]:
        await p.notify_voice_activity(active, capture_time)
        await p.send_audio(chunk, capture_time)
    assert [e["type"] for e in messages(p)] == ["input_audio_buffer.append"] * 5 + [
        "input_audio_buffer.commit"
    ]
    assert p._pending_commits == 1
    assert not p._has_audio


@pytest.mark.asyncio
async def test_finish_waits_for_all_turns_and_delivers_in_input_order():
    p = provider()
    await p.send_audio(bytes(4800), 0)
    await p._commit_audio()
    await p._handle_event(
        {"type": "input_audio_buffer.committed", "item_id": "one", "previous_item_id": None}
    )
    await p.send_audio(bytes(4800), 1)
    finish = asyncio.create_task(p.finish_utterance())
    await asyncio.sleep(0)
    assert not finish.done()
    await p._handle_event(
        {"type": "input_audio_buffer.committed", "item_id": "two", "previous_item_id": "one"}
    )
    await p._handle_event(
        {
            "type": "conversation.item.input_audio_transcription.completed",
            "item_id": "two",
            "transcript": "second",
        }
    )
    assert not finish.done()
    p.on_final.assert_not_called()
    await p._handle_event(
        {
            "type": "conversation.item.input_audio_transcription.completed",
            "item_id": "one",
            "transcript": "first",
        }
    )
    await finish
    assert [c.args[0] for c in p.on_final.call_args_list] == ["first", "second"]
    assert len([e for e in messages(p) if e["type"] == "input_audio_buffer.commit"]) == 2


@pytest.mark.asyncio
async def test_interleaved_deltas_are_isolated_and_duplicate_finals_ignored():
    p = provider()
    for item, previous in [("one", None), ("two", "one")]:
        await p._handle_event(
            {"type": "input_audio_buffer.committed", "item_id": item, "previous_item_id": previous}
        )
    for item, delta in [("one", "hello"), ("two", "later"), ("one", " world")]:
        await p._handle_event(
            {
                "type": "conversation.item.input_audio_transcription.delta",
                "item_id": item,
                "delta": delta,
            }
        )
    assert [c.args[0] for c in p.on_partial.call_args_list] == ["hello", "hello world"]
    for item, text in [("two", "later"), ("one", "hello world"), ("one", "hello world")]:
        await p._handle_event(
            {
                "type": "conversation.item.input_audio_transcription.completed",
                "item_id": item,
                "transcript": text,
            }
        )
    assert [c.args[0] for c in p.on_final.call_args_list] == ["hello world", "later"]


@pytest.mark.asyncio
async def test_no_audio_never_commits_and_short_phrase_is_padded():
    p = provider()
    await p.finish_utterance()
    p.ws.send.assert_not_called()
    await p.send_audio(bytes(960), 0)
    await p._commit_audio()
    sent = messages(p)
    assert len(base64.b64decode(sent[1]["audio"])) == 3840
    assert sent[2]["type"] == "input_audio_buffer.commit"


@pytest.mark.asyncio
async def test_gateway_headers_replace_direct_authentication():
    p = provider(
        headers={"cf-aig-authorization": "Bearer gateway-secret"}, provider_id="cloudflare"
    )
    p.ws = None
    with patch("websockets.connect", new_callable=AsyncMock) as connect:
        connect.return_value = AsyncMock()
        await p.start()
        assert connect.call_args.kwargs["additional_headers"] == {
            "cf-aig-authorization": "Bearer gateway-secret"
        }
        assert p.get_type() == "cloudflare"
        p._closing = True
        await p._close_transport()


@pytest.mark.asyncio
async def test_normal_remote_closure_reports_failure():
    p = provider()
    await p._receive_loop()
    assert not p.is_running
    p.on_error.assert_called_once()


@pytest.mark.asyncio
async def test_finish_timeout_is_bounded_and_reports_missing_final():
    p = provider()
    await p.send_audio(bytes(4800), 0)
    with pytest.raises(TimeoutError):
        await asyncio.wait_for(p.finish_utterance(), 0.5)
    assert not p.is_running
    assert p.on_error.call_args.args[0].title == "Transcription Delayed"
    await p._handle_event(
        {"type": "conversation.item.input_audio_transcription.completed", "transcript": "late"}
    )
    p.on_final.assert_not_called()


@pytest.mark.asyncio
async def test_api_error_reports_once_without_echoing_server_secrets():
    p = provider()
    await p._handle_event(
        {"type": "error", "error": {"code": "invalid_api_key", "message": "secret"}}
    )
    p.on_error.assert_called_once()
    error = p.on_error.call_args.args[0]
    assert error.title == "Auth Failed"
    assert "secret" not in error.message
    assert not p.is_running


@pytest.mark.asyncio
async def test_failed_turn_releases_later_successful_turn():
    p = provider()
    for item, previous in [("one", None), ("two", "one")]:
        await p._handle_event(
            {"type": "input_audio_buffer.committed", "item_id": item, "previous_item_id": previous}
        )
    await p._handle_event(
        {
            "type": "conversation.item.input_audio_transcription.completed",
            "item_id": "two",
            "transcript": "second",
        }
    )
    await p._handle_event(
        {"type": "conversation.item.input_audio_transcription.failed", "item_id": "one"}
    )
    p.on_final.assert_called_once_with("second")
    p.on_error.assert_called_once()
    assert p._drained.is_set()


@pytest.mark.asyncio
async def test_transport_failure_during_drain_raises_instead_of_reporting_success():
    p = provider()
    await p.send_audio(bytes(4800), 0)
    finish = asyncio.create_task(p.finish_utterance())
    await asyncio.sleep(0)
    p._fail_transport("Connection dropped during final transcription")
    with pytest.raises(ConnectionError, match="Connection dropped"):
        await finish
    p.on_error.assert_called_once()


@pytest.mark.asyncio
async def test_stop_closes_transport_after_expected_drain_timeout():
    p = provider()
    ws = p.ws
    await p.send_audio(bytes(4800), 0)
    await p._do_stop()
    ws.close.assert_awaited_once()
    assert p.ws is None
    assert not p.is_running


@pytest.mark.asyncio
@pytest.mark.parametrize("model", ["gpt-live-transcribe", "gpt-transcribe"])
async def test_local_pre_roll_preserves_soft_onset_and_short_pause_stays_in_turn(model):
    p = provider(model, prefix_padding_ms=100)
    quiet_chunk = bytes([1, 0]) * 2400
    await p.notify_voice_activity(False, 0)
    await p.send_audio(quiet_chunk, 0)
    await p.notify_voice_activity(False, 0.1)
    await p.send_audio(quiet_chunk, 0.1)
    p.ws.send.assert_not_called()
    assert len(p._prefix_audio) == 4800
    await p.notify_voice_activity(True, 0.2)
    await p.send_audio(bytes(4800), 0.2)
    assert base64.b64decode(messages(p)[0]["audio"]) == quiet_chunk
    await p.notify_voice_activity(False, 0.3)
    await p.send_audio(bytes(4800), 0.3)
    await p.notify_voice_activity(True, 0.4)
    await p.send_audio(bytes(4800), 0.4)
    assert all(e["type"] == "input_audio_buffer.append" for e in messages(p))
