import json
from urllib.parse import parse_qs, urlsplit

import pytest
from pydantic import ValidationError

from engine.config import CloudflareCoreConfig, Config
from engine.config_resolver import resolve_effective_config
from engine.transcription.factory import TranscriptionFactory
from engine.transcription.openai_provider import OpenAIProvider


def query(url):
    return parse_qs(urlsplit(url).query)


def test_assembly_36_preserves_context_and_modern_options():
    config = Config()
    core = config.providers.assemblyai.core
    core.speech_model = "universal-3-6-pro"
    core.language_codes = ["en", "ar"]
    core.agent_context = "Software engineering terminology"
    config.transcription.latency_profile = "fast"
    config.transcription.mic_profile = "headset"
    resolved = resolve_effective_config(config).assemblyai
    params = query(resolved.url)
    assert params["speech_model"] == ["universal-3-6-pro"]
    assert params["mode"] == ["min_latency"]
    assert params["voice_focus"] == ["near-field"]
    assert json.loads(params["language_codes"][0]) == ["en", "ar"]
    assert params["agent_context"] == [core.agent_context]
    assert "language_code" not in params
    assert "end_of_turn_confidence_threshold" not in params
    assert "format_turns" not in params


def test_assembly_existing_query_uses_actual_capture_rate():
    config = Config()
    config.providers.assemblyai.core.ws_url = (
        "wss://streaming.assemblyai.com/v3/ws?sample_rate=48000&custom=retained"
    )
    config.audio.capture_sample_rate = 16000
    resolved = resolve_effective_config(config).assemblyai
    params = query(resolved.url)
    assert resolved.sample_rate == 16000
    assert params["sample_rate"] == ["16000"]
    assert params["custom"] == ["retained"]


def test_openai_transcription_intent_with_existing_query():
    config = Config()
    config.providers.openai.core.realtime_ws_url_base = (
        "wss://api.openai.com/v1/realtime?intent=wrong&custom=retained"
    )
    params = query(resolve_effective_config(config).openai.url)
    assert params["intent"] == ["transcription"]
    assert params["custom"] == ["retained"]


@pytest.mark.parametrize("byok", [True, False])
def test_gateway_openai_reuses_adapter_and_correct_credentials(monkeypatch, byok):
    monkeypatch.setattr(Config, "get_cloudflare_key", lambda self: "cf-token")
    monkeypatch.setattr(Config, "get_openai_key", lambda self: "openai-key")
    config = Config()
    config.transcription.provider = "cloudflare"
    core = config.providers.cloudflare.core
    core.account_id = "a" * 32
    core.gateway_id = "my-gateway"
    core.model = "openai/gpt-live-transcribe"
    core.use_byok = byok
    core.language = "ar"
    adapter = TranscriptionFactory.create(config, lambda text: None, lambda text: None)
    assert isinstance(adapter, OpenAIProvider)
    assert adapter.get_type() == "cloudflare"
    effective = adapter.effective_config
    assert effective.transcription_model == "gpt-live-transcribe"
    assert effective.languages == ("ar",)
    assert urlsplit(effective.url).path == f"/v1/{'a' * 32}/my-gateway/openai"
    assert effective.headers["cf-aig-authorization"] == "Bearer cf-token"
    assert effective.headers["cf-aig-collect-log-payload"] == "false"
    if byok:
        assert "Authorization" not in effective.headers
    else:
        assert effective.headers["Authorization"] == "Bearer openai-key"


def test_gateway_local_key_required_without_byok(monkeypatch):
    monkeypatch.setattr(Config, "get_cloudflare_key", lambda self: "cf-token")
    monkeypatch.setattr(Config, "get_openai_key", lambda self: None)
    config = Config()
    config.transcription.provider = "cloudflare"
    core = config.providers.cloudflare.core
    core.account_id = "a" * 32
    core.model = "openai/gpt-transcribe"
    core.use_byok = False
    with pytest.raises(ValueError, match="OpenAI key"):
        TranscriptionFactory.create(config, lambda text: None, lambda text: None)


def test_grok_uses_unified_cloudflare_streaming_route(monkeypatch):
    from engine.transcription.grok_provider import GrokProvider

    monkeypatch.setattr(Config, "get_cloudflare_key", lambda self: "cf-token")
    config = Config()
    config.transcription.provider = "cloudflare"
    core = config.providers.cloudflare.core
    core.account_id = "a" * 32
    core.gateway_id = "speech"
    core.model = "xai/grok-stt"
    core.language = "en"
    adapter = TranscriptionFactory.create(config, lambda text: None, lambda text: None)
    assert isinstance(adapter, GrokProvider)
    effective = adapter.effective_config
    assert urlsplit(effective.url).hostname == "api.cloudflare.com"
    assert urlsplit(effective.url).path == f"/client/v4/accounts/{'a' * 32}/ai/run"
    parameters = query(effective.url)
    assert parameters["model"] == ["xai/grok-stt"]
    assert parameters["websocket"] == ["true"]
    assert parameters["audio_format"] == ["pcm"]
    assert parameters["sample_rate"] == ["16000"]
    assert parameters["language"] == ["en"]
    assert effective.gateway_id == "speech"


@pytest.mark.parametrize(
    "settings",
    [
        {"account_id": "https://example.com"},
        {"gateway_id": "../bad"},
        {"model": "arbitrary-chat-model"},
        {"endpointing_ms": 0},
        {"api_token": "secret"},
    ],
)
def test_gateway_core_rejects_invalid_settings_and_secrets(settings):
    with pytest.raises(ValidationError):
        CloudflareCoreConfig.model_validate(settings)


def test_save_gateway_settings_separates_token_from_toml(monkeypatch, tmp_path):
    from engine.gui_main import save_cloudflare_settings

    stored = []
    monkeypatch.setattr(
        "engine.gui_main.SecurityManager.set_key",
        lambda account, token: stored.append((account, token)),
    )
    config = Config()
    target = tmp_path / "config.toml"
    save = Config.save
    monkeypatch.setattr(
        Config, "save", lambda self, path=None, blocking=False: save(self, path, blocking=True)
    )
    monkeypatch.setattr("engine.config.get_config_path", lambda: str(target))
    save_cloudflare_settings(
        config,
        {
            "core": {"account_id": "a" * 32, "gateway_id": "speech", "model": "@cf/deepgram/flux"},
            "api_token": "private-token-never-in-toml",
        },
    )
    config.save(target, blocking=True)
    assert stored == [("cloudflare_api_token", "private-token-never-in-toml")]
    serialized = target.read_text(encoding="utf-8")
    assert "private-token" not in serialized
    assert "api_token" not in serialized
    saved = Config.from_file(target)
    assert saved.providers.cloudflare.core.gateway_id == "speech"
    assert saved.providers.cloudflare.core.model == "@cf/deepgram/flux"


def test_save_gateway_settings_blank_token_keeps_stored_credential(monkeypatch):
    from engine.gui_main import save_cloudflare_settings

    calls = []
    monkeypatch.setattr("engine.gui_main.SecurityManager.set_key", lambda *args: calls.append(args))
    monkeypatch.setattr(Config, "update_and_save", lambda *args, **kwargs: None)
    save_cloudflare_settings(Config(), {"core": {"gateway_id": "speech"}, "api_token": None})
    assert calls == []


def test_save_gateway_settings_validation_precedes_token_store(monkeypatch):
    from engine.gui_main import save_cloudflare_settings

    calls = []
    monkeypatch.setattr("engine.gui_main.SecurityManager.set_key", lambda *args: calls.append(args))
    with pytest.raises(ValidationError):
        save_cloudflare_settings(
            Config(), {"core": {"gateway_id": "../bad"}, "api_token": "secret"}
        )
    assert calls == []
