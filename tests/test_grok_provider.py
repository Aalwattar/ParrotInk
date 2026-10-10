import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from engine.transcription.grok_provider import GrokProvider


def provider():
    cfg = SimpleNamespace(
        url="wss://api.cloudflare.com/client/v4/accounts/account/ai/run?model=xai/grok-stt",
        gateway_id="dictation",
        sample_rate=16000,
        stop_timeout=0.2,
        is_test=False,
    )
    p = GrokProvider("secret", Mock(), Mock(), cfg, on_status=Mock(), on_error=Mock())
    p.ws = AsyncMock()
    p._is_running = True
    p._ready_event.set()
    return p


def result(text, start=0, duration=1, final=False, speech_final=False):
    return {
        "type": "transcript.partial",
        "text": text,
        "start": start,
        "duration": duration,
        "is_final": final,
        "speech_final": speech_final,
    }


@pytest.mark.asyncio
async def test_start_waits_for_created_and_uses_gateway_headers():
    p = provider()
    block = asyncio.Event()

    async def incoming():
        await block.wait()
        if False:
            yield ""

    p.ws.__aiter__.side_effect = incoming
    with (
        patch(
            "engine.transcription.grok_provider.SecurityManager.is_url_trusted", return_value=True
        ),
        patch(
            "engine.transcription.grok_provider.websockets.connect",
            new=AsyncMock(return_value=p.ws),
        ) as connect,
    ):
        await p.start()
        assert not p._ready_event.is_set()
        headers = connect.call_args.kwargs["additional_headers"]
        assert headers == {
            "Authorization": "Bearer secret",
            "cf-aig-gateway-id": "dictation",
            "cf-aig-collect-log-payload": "false",
        }
        with pytest.raises(ConnectionError):
            await p.send_audio(b"audio", 0)
        await p._handle_event({"type": "transcript.created"})
        await p.wait_for_ready()
        await p.send_audio(b"audio", 0)
        p.ws.send.assert_awaited_once_with(b"audio")
        await p.stop()


@pytest.mark.asyncio
async def test_untrusted_route_never_connects():
    p = provider()
    with (
        patch(
            "engine.transcription.grok_provider.SecurityManager.is_url_trusted", return_value=False
        ),
        patch("engine.transcription.grok_provider.websockets.connect", new=AsyncMock()) as connect,
    ):
        with pytest.raises(ConnectionError, match="Untrusted"):
            await p.start()
        connect.assert_not_awaited()


@pytest.mark.asyncio
async def test_chunk_final_and_stitched_utterance_do_not_duplicate():
    p = provider()
    await p._handle_event(result("hello", final=True))
    await p._handle_event(result("there", start=1, final=True))
    p.on_final.assert_not_called()
    assert p.on_partial.call_args.args == ("hello there",)
    utterance = result("hello there", duration=2, final=True, speech_final=True)
    await p._handle_event(utterance)
    await p._handle_event(utterance)
    await p._handle_event(result("late", final=False))
    p.on_final.assert_called_once_with("hello there")
    assert p.on_partial.call_count == 2


@pytest.mark.asyncio
async def test_repeated_identical_phrases_have_distinct_timestamps():
    p = provider()
    await p._handle_event(result("yes", final=True, speech_final=True))
    await p._handle_event(result("yes", start=2, final=True, speech_final=True))
    assert p.on_final.call_count == 2


@pytest.mark.asyncio
async def test_terminal_done_injects_only_pending_phrase_using_words():
    p = provider()
    await p._handle_event(result("Yes.", final=True, speech_final=True))
    await p._handle_event(
        {
            "type": "transcript.done",
            "text": "Yes. Yes.",
            "duration": 3,
            "words": [{"text": "Yes.", "start": 0.2}, {"text": "Yes.", "start": 2.1}],
        }
    )
    assert [call.args[0] for call in p.on_final.call_args_list] == ["Yes.", "Yes."]
    assert not p.is_running
    assert not p._failure_event.is_set()


@pytest.mark.asyncio
async def test_terminal_done_without_words_strips_session_prefix():
    p = provider()
    await p._handle_event(result("first phrase", final=True, speech_final=True))
    await p._handle_event({"type": "transcript.done", "text": "first phrase second phrase"})
    assert [call.args[0] for call in p.on_final.call_args_list] == ["first phrase", "second phrase"]


@pytest.mark.asyncio
async def test_terminal_done_does_not_repeat_already_injected_session():
    p = provider()
    await p._handle_event(result("hello", final=True, speech_final=True))
    await p._handle_event({"type": "transcript.done", "text": "hello"})
    p.on_final.assert_called_once_with("hello")


@pytest.mark.asyncio
async def test_finish_waits_for_done_after_earlier_phrase_final():
    p = provider()
    await p.send_audio(b"first phrase", 0)
    await p.send_audio(b"next phrase", 1)
    await p._handle_event(result("first phrase", final=True, speech_final=True))
    assert p._has_audio
    finish = asyncio.create_task(p.finish_utterance())
    try:
        await asyncio.sleep(0)
        assert p.ws.send.call_args.args[0] == json.dumps({"type": "audio.done"})
        await p._handle_event(result("next phrase", start=2, final=True, speech_final=True))
        await asyncio.sleep(0)
        assert not finish.done()
        await p._handle_event({"type": "transcript.done", "text": "first phrase next phrase"})
        await finish
        assert not p.is_running
        await p.finish_utterance()
        assert p.ws.send.await_count == 3
    finally:
        finish.cancel()
        await asyncio.gather(finish, return_exceptions=True)


@pytest.mark.asyncio
async def test_finish_timeout_signals_failure():
    p = provider()
    await p.send_audio(b"audio", 0)
    with pytest.raises(TimeoutError):
        await p.finish_utterance()
    assert p._failure_event.is_set()
    assert not p.is_running
    p.on_error.assert_called_once()


@pytest.mark.asyncio
async def test_cancelled_finish_signals_failure():
    p = provider()
    finish = asyncio.create_task(p.finish_utterance())
    await asyncio.sleep(0)
    finish.cancel()
    with pytest.raises(asyncio.CancelledError):
        await finish
    assert p._failure_event.is_set()


@pytest.mark.asyncio
async def test_error_is_sanitized_and_wakes_finish():
    p = provider()
    finish = asyncio.create_task(p.finish_utterance())
    await asyncio.sleep(0)
    await p._handle_event({"type": "error", "message": "secret echoed by server"})
    with pytest.raises(ConnectionError):
        await finish
    p.on_error.assert_called_once()
    assert "secret" not in p.on_error.call_args.args[0].message


@pytest.mark.asyncio
@pytest.mark.parametrize("expected", [False, True])
async def test_receive_close_is_expected_only_after_done(expected):
    p = provider()

    async def messages():
        if expected:
            yield json.dumps({"type": "transcript.done", "text": "hello"})

    p.ws.__aiter__.side_effect = messages
    await p._receive_loop()
    assert p._failure_event.is_set() is not expected
    assert p.on_error.call_count == (0 if expected else 1)


@pytest.mark.asyncio
async def test_stop_cancels_receiver_even_when_socket_close_fails():
    p = provider()
    p._receive_task = asyncio.create_task(asyncio.Event().wait())
    receiver = p._receive_task
    p.ws.close.side_effect = RuntimeError("close failed")
    await p.stop()
    assert receiver.cancelled()
    assert p.ws is None
    assert not p.is_running


@pytest.mark.asyncio
async def test_stop_timeout_still_cancels_receiver_and_releases_socket():
    p = provider()
    p._receive_task = asyncio.create_task(asyncio.Event().wait())
    receiver = p._receive_task

    async def blocked_close():
        await asyncio.Event().wait()

    p.ws.close.side_effect = blocked_close
    await p.stop()
    assert receiver.cancelled()
    assert p.ws is None
    assert not p.is_running


@pytest.mark.asyncio
async def test_ready_wait_fails_on_server_error():
    p = provider()
    p._ready_event.clear()
    ready = asyncio.create_task(p.wait_for_ready())
    await p._handle_event({"type": "error", "message": "credential secret"})
    with pytest.raises(ConnectionError):
        await ready


@pytest.mark.asyncio
async def test_send_failure_is_sanitized_and_string_audio_is_rejected():
    p = provider()
    with pytest.raises(TypeError):
        await p.send_audio("base64", 0)
    p.ws.send.side_effect = RuntimeError("secret transport error")
    with pytest.raises(ConnectionError, match="transport failed"):
        await p.send_audio(b"pcm", 0)
    assert "secret" not in p.on_error.call_args.args[0].message


def test_audio_spec_and_reset_preserve_pending_audio():
    p = provider()
    assert p.get_audio_spec().sample_rate_hz == 16000
    assert p.get_audio_spec().wire_encoding == "pcm16_bytes"
    p._has_audio = True
    p.reset_utterance()
    assert p._has_audio


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [401, 403])
async def test_grok_auth_failure_explains_required_token_permission(status):
    from websockets.datastructures import Headers
    from websockets.exceptions import InvalidStatus
    from websockets.http11 import Response

    p = provider()
    failure = InvalidStatus(Response(status, "Denied", Headers(), b"secret"))
    with patch(
        "engine.transcription.grok_provider.websockets.connect",
        new=AsyncMock(side_effect=failure),
    ):
        with pytest.raises(ConnectionError, match="Workers AI.*Read") as error:
            await p.start()
        assert "secret" not in str(error.value)
        assert p._failure_event.is_set()


@pytest.mark.asyncio
async def test_empty_done_acknowledges_already_delivered_final():
    p = provider()
    await p.send_audio(b"audio", 0)
    await p._handle_event(result("complete phrase", final=True, speech_final=True))
    await p._handle_event({"type": "transcript.done", "duration": 1})
    p.on_final.assert_called_once_with("complete phrase")
    p.on_error.assert_not_called()
    assert p._done_received and not p.is_running


@pytest.mark.asyncio
async def test_empty_done_delivers_locked_chunks_without_repeating_earlier_phrase():
    p = provider()
    await p._handle_event(result("first phrase", final=True, speech_final=True))
    await p._handle_event(result("remaining words", start=1, final=True, speech_final=False))
    await p._handle_event({"type": "transcript.done", "duration": 2})
    assert [call.args[0] for call in p.on_final.call_args_list] == [
        "first phrase",
        "remaining words",
    ]
    assert p._done_received
