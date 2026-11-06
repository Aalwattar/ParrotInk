import asyncio
import base64
import io
import json
import wave
from dataclasses import replace
from unittest.mock import Mock

import httpx
import pytest

from engine.config import Config
from engine.config_resolver import resolve_effective_config
from engine.transcription.factory import TranscriptionFactory
from engine.transcription.openrouter_provider import OpenRouterProvider


@pytest.fixture
def provider(monkeypatch):
    config = Config()
    config.transcription.provider = "cloudflare"
    config.providers.cloudflare.core.account_id = "a" * 32
    config.providers.cloudflare.core.model = "microsoft/mai-transcribe-2"
    monkeypatch.setattr(Config, "get_cloudflare_key", lambda self: "test-secret")
    result = TranscriptionFactory.create(config, Mock(), Mock(), on_error=Mock())
    assert isinstance(result, OpenRouterProvider)
    assert result.base_url.endswith("/default/openrouter/audio/transcriptions")
    return result


async def connect(provider, monkeypatch, handler):
    client_type = httpx.AsyncClient

    def client(**kwargs):
        return client_type(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client)
    await provider.start()
    await provider.wait_for_ready()


async def test_record_submit_and_reuse(provider, monkeypatch):
    requests = []

    def handle(request):
        requests.append(request)
        body = json.loads(request.content)
        assert body["model"] == "microsoft/mai-transcribe-2"
        assert body["language"] == "en"
        with wave.open(io.BytesIO(base64.b64decode(body["input_audio"]["data"]))) as audio:
            assert (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) == (
                1,
                2,
                16000,
            )
            assert audio.readframes(100) == b"\x01\x00" * 10
        assert request.headers["cf-aig-authorization"] == "Bearer test-secret"
        assert "authorization" not in request.headers
        assert request.headers["cf-aig-collect-log-payload"] == "false"
        assert request.headers["user-agent"] == "ParrotInk/1.0"
        return httpx.Response(200, json={"text": "hello"})

    provider.effective_config = replace(provider.effective_config, language="en")
    await connect(provider, monkeypatch, handle)
    for _ in range(2):
        provider.reset_utterance()
        await provider.send_audio(b"\x01\x00" * 10, 0)
        assert len(requests) == provider.on_final.call_count
        await provider.finish_utterance()
        await provider.finish_utterance()
    assert len(requests) == 2
    assert provider.on_final.call_count == 2
    provider.on_partial.assert_not_called()
    await provider.stop()
    assert not provider.is_running
    assert not provider._audio


@pytest.mark.parametrize(
    "status,word",
    [
        (402, "credit"),
        (401, "key"),
        (403, "denied"),
        (413, "large"),
        (429, "limited"),
        (500, "HTTP 500"),
    ],
)
async def test_errors_are_safe_and_actionable(provider, monkeypatch, status, word):
    await connect(
        provider,
        monkeypatch,
        lambda request: httpx.Response(status, text="sensitive transcript and test-secret"),
    )
    await provider.send_audio(bytes(320), 0)
    with pytest.raises(ConnectionError, match=word):
        await provider.finish_utterance()
    error = provider.on_error.call_args.args[0]
    assert word in error.message
    assert "test-secret" not in error.message
    provider.on_final.assert_not_called()
    assert not provider._audio
    assert not provider.is_running
    await provider.stop()


@pytest.mark.parametrize("body", [{}, {"text": None}, ["text"], "not json"])
async def test_malformed_response(provider, monkeypatch, body):
    await connect(provider, monkeypatch, lambda request: httpx.Response(200, json=body))
    await provider.send_audio(bytes(320), 0)
    with pytest.raises(ConnectionError):
        await provider.finish_utterance()
    provider.on_final.assert_not_called()
    await provider.stop()


async def test_reset_and_stop_discard_audio_without_upload(provider, monkeypatch):
    handler = Mock(return_value=httpx.Response(200, json={"text": ""}))
    await connect(provider, monkeypatch, handler)
    await provider.send_audio(bytes(320), 0)
    provider.reset_utterance()
    await provider.finish_utterance()
    await provider.send_audio(bytes(320), 0)
    await provider.stop()
    handler.assert_not_called()
    assert not provider._audio


async def test_stop_cancels_pending_upload(provider, monkeypatch):
    entered = asyncio.Event()

    async def handle(request):
        entered.set()
        await asyncio.Event().wait()

    await connect(provider, monkeypatch, handle)
    await provider.send_audio(bytes(320), 0)
    task = asyncio.create_task(provider.finish_utterance())
    await entered.wait()
    await provider.stop()
    with pytest.raises(asyncio.CancelledError):
        await task
    provider.on_final.assert_not_called()
    assert not provider._audio


async def test_timeout(provider, monkeypatch):
    def handle(request):
        raise httpx.ReadTimeout("sensitive server details")

    await connect(provider, monkeypatch, handle)
    await provider.send_audio(bytes(320), 0)
    with pytest.raises(TimeoutError, match="timed out"):
        await provider.finish_utterance()
    assert "sensitive" not in provider.on_error.call_args.args[0].message
    await provider.stop()


async def test_recording_size_limit(provider, monkeypatch):
    await connect(provider, monkeypatch, Mock())
    provider.MAX_AUDIO_BYTES = 4
    await provider.send_audio(bytes(4), 0)
    with pytest.raises(ValueError, match="too long"):
        await provider.send_audio(bytes(2), 0)
    assert not provider._audio
    await provider.stop()


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.com",
        "http://gateway.ai.cloudflare.com",
        "https://api.openai.com",
        "https://user@gateway.ai.cloudflare.com",
    ],
)
async def test_rejects_unsafe_credential_destinations(provider, url):
    provider.base_url = url
    with pytest.raises(ConnectionError, match="Untrusted"):
        await provider.start()


def test_local_mock_uses_http():
    config = Config()
    config.providers.cloudflare.core.model = "microsoft/mai-transcribe-2"
    config.test.enabled = True
    assert resolve_effective_config(config).cloudflare.url == "http://localhost:8081"
