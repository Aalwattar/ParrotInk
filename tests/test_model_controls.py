from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from engine.config import Config, OpenAICoreConfig
from engine.config_resolver import resolve_effective_config
from engine.transcription.catalog import get_model
from engine.transcription.factory import TranscriptionFactory


@pytest.mark.parametrize("model", ["gpt-transcribe", "gpt-live-transcribe"])
@pytest.mark.parametrize(
    "profile,delay,silence",
    [("fast", "low", 300), ("balanced", "medium", 500), ("accurate", "high", 800)],
)
@pytest.mark.parametrize(
    "mic,noise", [("none", None), ("headset", "near_field"), ("laptop", "far_field")]
)
def test_both_transcription_models_apply_speed_and_microphone_profiles(
    monkeypatch, model, profile, delay, silence, mic, noise
):
    monkeypatch.setattr(Config, "get_openai_key", lambda self: None)
    config = Config()
    config.test.enabled = True
    config.transcription.provider = "openai"
    config.transcription.latency_profile = profile
    config.transcription.mic_profile = mic
    config.providers.openai.core.transcription_model = model
    adapter = TranscriptionFactory.create(config, lambda text: None, lambda text: None)
    effective = adapter.effective_config
    assert effective.transcription_model == model
    assert effective.delay == delay
    assert effective.silence_duration_ms == silence
    assert effective.noise_reduction_type == noise


@pytest.mark.parametrize("model", ["gpt-live-1", "gpt-realtime-2.1", "gpt-6-astra"])
def test_conversational_models_cannot_be_selected_for_transcription(model):
    with pytest.raises(ValidationError):
        OpenAICoreConfig(transcription_model=model)


@pytest.mark.asyncio
@pytest.mark.parametrize("model", ["gpt-transcribe", "gpt-live-transcribe"])
async def test_modern_models_create_transcription_only_sessions(model):
    import json

    from engine.transcription.openai_provider import OpenAIProvider

    config = Config()
    config.providers.openai.core.transcription_model = model
    provider = OpenAIProvider(
        "", lambda text: None, lambda text: None, resolve_effective_config(config).openai
    )
    provider.ws = AsyncMock()
    await provider._update_session()
    payload = json.loads(provider.ws.send.call_args.args[0])
    assert payload["session"]["type"] == "transcription"
    assert payload["session"]["audio"]["input"]["transcription"]["model"] == model
    assert "tools" not in payload["session"]


def test_transcribe_menu_uses_the_model_name_without_phrase_jargon():
    assert get_model("openai", "gpt-transcribe").label == "GPT Transcribe"


def test_provider_event_refreshes_the_matching_model_menu(mocker):
    from engine.ui import TrayApp
    from engine.ui_bridge import UIEvent

    config = Config()
    config.transcription.provider = "cloudflare"
    mocker.patch("engine.ui.pystray.Icon")
    mocker.patch.object(TrayApp, "_ensure_indicator", return_value=False)
    app = TrayApp(config, initial_provider="openai")
    app.bridge = mocker.Mock()
    app.bridge.get_event.side_effect = [
        (UIEvent.UPDATE_PROVIDER, "cloudflare"),
        (UIEvent.QUIT, None),
    ]
    app._poll_bridge()
    assert app.current_provider == "cloudflare"
    transcription = next(item for item in app.icon.menu if item.text.startswith("Transcription"))
    models = next(item for item in transcription.submenu if item.text == "Model")
    assert list(models.submenu)[0].text == "Nova-3 (Cloudflare hosted)"
