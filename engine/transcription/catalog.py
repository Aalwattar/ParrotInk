"""Supported transcription models and the protocols each adapter understands."""

from dataclasses import dataclass, replace
from typing import Any


@dataclass(frozen=True)
class ModelSpec:
    id: str
    label: str
    provider: str
    protocol: str
    modern: bool = True
    diarization: bool = False


PROVIDER_LABELS = {
    "openai": "OpenAI",
    "assemblyai": "AssemblyAI",
    "cloudflare": "Cloudflare AI Gateway",
}

MODELS = (
    ModelSpec("gpt-live-transcribe", "GPT Live Transcribe", "openai", "openai"),
    ModelSpec("gpt-transcribe", "GPT Transcribe", "openai", "openai"),
    ModelSpec("gpt-4o-mini-transcribe", "GPT-4o Mini (legacy)", "openai", "openai", False),
    ModelSpec("gpt-4o-transcribe", "GPT-4o Transcribe (legacy)", "openai", "openai", False),
    ModelSpec("universal-3-6-pro", "Universal 3.6 Pro", "assemblyai", "assemblyai", True, True),
    ModelSpec("universal-3-5-pro", "Universal 3.5 Pro", "assemblyai", "assemblyai", True, True),
    ModelSpec("u3-rt-pro", "Universal 3 Pro (legacy)", "assemblyai", "assemblyai", True, True),
    ModelSpec(
        "universal-streaming-english", "Universal English", "assemblyai", "assemblyai", False
    ),
    ModelSpec(
        "universal-streaming-multilingual",
        "Universal Multilingual",
        "assemblyai",
        "assemblyai",
        False,
    ),
    ModelSpec("whisper-rt", "Whisper Streaming (legacy)", "assemblyai", "assemblyai", False),
    ModelSpec(
        "@cf/deepgram/nova-3",
        "Nova-3 (Cloudflare hosted)",
        "cloudflare",
        "deepgram_nova",
        True,
        True,
    ),
    ModelSpec("@cf/deepgram/flux", "Flux (Cloudflare hosted)", "cloudflare", "deepgram_flux"),
    ModelSpec("xai/grok-stt", "Grok Speech-to-Text", "cloudflare", "grok_stt"),
    # Retain old configuration IDs without offering unavailable Unified Billing routes.
    ModelSpec(
        "openai/gpt-live-transcribe", "OpenAI GPT Live Transcribe", "cloudflare", "unavailable"
    ),
    ModelSpec("openai/gpt-transcribe", "OpenAI GPT Transcribe", "cloudflare", "unavailable"),
)


def models_for_provider(provider: str) -> tuple[ModelSpec, ...]:
    return tuple(
        model for model in MODELS if model.provider == provider and model.protocol != "unavailable"
    )


def get_model(provider: str, model_id: str) -> ModelSpec:
    if provider == "openai" and model_id in {
        "gpt-4o-mini-transcribe-2025-03-20",
        "gpt-4o-mini-transcribe-2025-12-15",
    }:
        return replace(get_model(provider, "gpt-4o-mini-transcribe"), id=model_id)
    for model in MODELS:
        if model.provider == provider and model.id == model_id:
            return model
    raise ValueError(f"Unsupported transcription model '{model_id}' for {provider}")


def get_selected_model(config: Any, provider: str) -> str:
    if provider not in PROVIDER_LABELS:
        return "Unknown"
    core = getattr(config.providers, provider).core
    field = {"openai": "transcription_model", "assemblyai": "speech_model", "cloudflare": "model"}
    return str(getattr(core, field[provider]))


def model_config_update(provider: str, model: str) -> dict:
    get_model(provider, model)
    field = {"openai": "transcription_model", "assemblyai": "speech_model", "cloudflare": "model"}
    return {"providers": {provider: {"core": {field[provider]: model}}}}
