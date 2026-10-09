import asyncio
import json
from unittest.mock import AsyncMock, Mock

import pytest

from engine.app_types import EffectiveCloudflareConfig
from engine.transcription.cloudflare_provider import CloudflareProvider


def provider(protocol="deepgram_nova"):
    cfg = EffectiveCloudflareConfig(
        url="wss://gateway.ai.cloudflare.com/v1/account/default/workers-ai",
        model="@cf/deepgram/nova-3",
        protocol=protocol,
        sample_rate=16000,
        language="",
        endpointing_ms=500,
        stop_timeout=0.2,
        is_test=False,
    )
    p = CloudflareProvider("secret", Mock(), Mock(), cfg, on_error=Mock())
    p.ws = AsyncMock()
    p._is_running = True
    return p


def nova(text, **fields):
    return {
        "type": "Results",
        "channel": {"alternatives": [{"transcript": text}]},
        "start": 0,
        "duration": 1,
        "channel_index": [0, 1],
        **fields,
    }


@pytest.mark.asyncio
async def test_nova_segments_deduplicate_and_flush_ack():
    p = provider()
    await p._handle_event(nova("hel", is_final=False))
    await p._handle_event(nova("hello", is_final=True))
    await p._handle_event(nova("hello", is_final=True))
    await p._handle_event(nova("", is_final=True, from_finalize=True))
    p.on_partial.assert_called_once_with("hel")
    p.on_final.assert_called_once_with("hello")
    assert p._finalized.is_set()


@pytest.mark.asyncio
async def test_same_text_in_different_segments_is_preserved():
    p = provider()
    await p._handle_event(nova("yes", is_final=True))
    await p._handle_event(nova("yes", is_final=True, start=2))
    assert p.on_final.call_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("protocol", ["deepgram_nova", "deepgram_flux"])
@pytest.mark.parametrize("older_final_after_flush", [False, True])
async def test_earlier_turn_final_does_not_discard_next_phrase(protocol, older_final_after_flush):
    p = provider(protocol)

    def partial(text, turn):
        if protocol == "deepgram_nova":
            return nova(text, start=turn, is_final=False)
        return {"type": "TurnInfo", "event": "Update", "turn_index": turn, "transcript": text}

    def final(text, turn, flushed=False):
        if protocol == "deepgram_nova":
            return nova(text, start=turn, is_final=True, speech_final=True, from_finalize=flushed)
        return {"type": "TurnInfo", "event": "EndOfTurn", "turn_index": turn, "transcript": text}

    await p.send_audio(b"first phrase", 0)
    await p._handle_event(partial("first", 0))
    await p.send_audio(b"second phrase", 1)
    if not older_final_after_flush:
        await p._handle_event(final("first phrase", 0))
    await p._handle_event(partial("second", 1))
    assert p._has_audio

    finish = asyncio.create_task(p.finish_utterance())
    try:
        await asyncio.sleep(0)
        expected = "Finalize" if protocol == "deepgram_nova" else "ForceEndTurn"
        assert p.ws.send.call_args.args[0] == json.dumps({"type": expected})
        if older_final_after_flush:
            await p._handle_event(final("first phrase", 0))
        await asyncio.sleep(0)
        assert not finish.done()
        assert p._pending_result
        assert not p._finalized.is_set()
        await p._handle_event(final("second phrase", 1, flushed=True))
        await finish
        assert [call.args[0] for call in p.on_final.call_args_list] == [
            "first phrase",
            "second phrase",
        ]
        assert not p._has_audio
    finally:
        if not finish.done():
            finish.cancel()
        await asyncio.gather(finish, return_exceptions=True)


@pytest.mark.asyncio
async def test_flux_turn_order_and_duplicate_finals():
    p = provider("deepgram_flux")
    await p._handle_event({"type": "Connected"})
    assert p._ready_event.is_set()
    await p._handle_event(
        {"type": "TurnInfo", "event": "Update", "turn_index": 0, "transcript": "hello"}
    )
    for _ in range(2):
        await p._handle_event(
            {"type": "TurnInfo", "event": "EndOfTurn", "turn_index": 0, "transcript": "hello there"}
        )
    await p._handle_event(
        {"type": "TurnInfo", "event": "Update", "turn_index": 0, "transcript": "late"}
    )
    p.on_partial.assert_called_once_with("hello")
    p.on_final.assert_called_once_with("hello there")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("protocol", "message"),
    [
        ("deepgram_nova", "Finalize"),
        ("deepgram_flux", "ForceEndTurn"),
    ],
)
async def test_finish_waits_for_final_result(protocol, message):
    p = provider(protocol)
    p._has_audio = True
    task = asyncio.create_task(p.finish_utterance())
    await asyncio.sleep(0)
    assert not task.done()
    p.ws.send.assert_awaited_once_with(json.dumps({"type": message}))
    if protocol == "deepgram_nova":
        await p._handle_event(nova("hello", is_final=True, from_finalize=True))
    else:
        await p._handle_event(
            {"type": "TurnInfo", "event": "EndOfTurn", "turn_index": 0, "transcript": "hello"}
        )
    await task
    p.on_final.assert_called_once_with("hello")


@pytest.mark.asyncio
async def test_error_is_sanitized_and_marks_unhealthy():
    p = provider()
    await p._handle_event({"type": "Error", "description": "secret echoed by server"})
    assert not p.is_running
    assert "secret" not in p.on_error.call_args.args[0].message


@pytest.mark.asyncio
async def test_connection_auth_and_no_premature_flux_readiness(monkeypatch):
    p = provider("deepgram_flux")
    p.ws.__aiter__.return_value = []
    connect = AsyncMock(return_value=p.ws)
    monkeypatch.setattr("engine.transcription.cloudflare_provider.websockets.connect", connect)
    await p.start()
    assert not p._ready_event.is_set()
    assert connect.call_args.kwargs["additional_headers"] == {
        "cf-aig-authorization": "Bearer secret",
        "cf-aig-collect-log-payload": "false",
    }
    await p._do_stop()


@pytest.mark.asyncio
async def test_rejects_untrusted_endpoint(monkeypatch):
    p = provider()
    monkeypatch.setattr(
        "engine.transcription.cloudflare_provider.SecurityManager.is_url_trusted",
        lambda *args, **kwargs: False,
    )
    with pytest.raises(ConnectionError, match="Untrusted"):
        await p.start()


@pytest.mark.asyncio
async def test_pending_transcript_timeout_prevents_reuse_and_late_delivery():
    p = provider()
    p.stop_timeout = 0.01
    p._has_audio = True
    await p._handle_event(nova("unfinished", is_final=False))
    with pytest.raises(TimeoutError, match="final transcript"):
        await p.finish_utterance()
    assert not p.is_running
    await p._handle_event(nova("late transcript", is_final=True))
    p.on_final.assert_not_called()
    p.on_error.assert_called_once()


@pytest.mark.asyncio
async def test_nova_already_final_without_flush_ack_is_not_failure():
    p = provider()
    p.stop_timeout = 0.01
    p._has_audio = True
    await p._handle_event(nova("already final", is_final=True))
    await p.finish_utterance()
    assert p.is_running
    p.on_error.assert_not_called()


@pytest.mark.asyncio
async def test_flux_already_final_accepts_no_active_turn_acknowledgement():
    p = provider("deepgram_flux")
    await p.send_audio(b"finished phrase", 0)
    await p._handle_event(
        {"type": "TurnInfo", "event": "EndOfTurn", "turn_index": 0, "transcript": "finished"}
    )
    finish = asyncio.create_task(p.finish_utterance())
    await asyncio.sleep(0)
    await p._handle_event({"type": "Warning", "code": "FORCE_END_TURN_NO_ACTIVE_TURN"})
    await finish
    assert not p._has_audio
    assert p.is_running
    p.on_error.assert_not_called()


@pytest.mark.asyncio
async def test_reset_keeps_session_dedup_but_clears_local_pending_audio():
    p = provider()
    await p._handle_event(nova("final", is_final=True))
    p._has_audio = True
    p.reset_utterance()
    assert not p._has_audio
    assert not p._pending_result
    await p._handle_event(nova("final", is_final=True))
    p.on_final.assert_called_once_with("final")


@pytest.mark.asyncio
async def test_transport_close_failure_still_clears_resources():
    p = provider()
    p.ws.close.side_effect = ConnectionError("failed")
    with pytest.raises(ConnectionError):
        await p._do_stop()
    assert p.ws is None
    assert not p.is_running
