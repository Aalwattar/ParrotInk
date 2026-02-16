from typing import Any, Optional

from .app_types import EffectiveAssemblyAIConfig, EffectiveConfig, EffectiveOpenAIConfig
from .config import LATENCY_PROFILES, MIC_PROFILES, Config


def resolve_effective_config(config: Config) -> EffectiveConfig:
    """
    Transforms the user-facing Config (Pydantic) into a resolved EffectiveConfig.
    Handles profiles, overrides, and engine-level invariants.
    """
    trans = config.transcription

    # 1. Resolve Shared Mappings
    profile = LATENCY_PROFILES.get(trans.latency_profile, LATENCY_PROFILES["balanced"])

    # 2. Resolve OpenAI
    openai_core = config.providers.openai.core
    openai_adv = config.providers.openai.advanced

    # Precedence: Override > Profile > Default
    noise_reduction: Optional[str] = None
    if openai_adv.override:
        openai_vad = openai_adv.vad_threshold
        openai_silence = openai_adv.silence_duration_ms
        noise_reduction = openai_adv.noise_reduction
        if noise_reduction == "off":
            noise_reduction = None
    else:
        openai_vad = float(profile["openai"]["vad_threshold"])
        openai_silence = int(profile["openai"]["silence_duration_ms"])
        # Use the profile mapping, defaulting to None (off) if somehow missing
        noise_reduction = MIC_PROFILES.get(trans.mic_profile)

    # Invariant: Must use the transcription intent in the URL
    openai_url = f"{openai_core.realtime_ws_url_base}?intent=transcription"
    if config.test.enabled:
        openai_url = config.test.openai_mock_url

    resolved_openai = EffectiveOpenAIConfig(
        url=openai_url,
        transcription_model=openai_core.transcription_model,
        prompt=openai_adv.prompt,
        turn_detection_type=openai_adv.turn_detection_type,
        vad_threshold=openai_vad,
        silence_duration_ms=openai_silence,
        prefix_padding_ms=openai_adv.prefix_padding_ms,
        noise_reduction_type=noise_reduction,
        language=openai_core.language,
        is_test=config.test.enabled,
    )

    # 3. Resolve AssemblyAI
    aai_core = config.providers.assemblyai.core
    aai_adv = config.providers.assemblyai.advanced

    if aai_adv.override:
        aai_confidence = aai_adv.end_of_turn_confidence_threshold
        aai_min_silence = aai_adv.min_end_of_turn_silence_when_confident_ms
        aai_max_silence = aai_adv.max_turn_silence_ms
    else:
        aai_params = profile["assemblyai"]
        aai_confidence = float(aai_params["end_of_turn_confidence_threshold"])
        aai_min_silence = int(aai_params["min_end_of_turn_silence_when_confident_ms"])
        aai_max_silence = int(aai_params["max_turn_silence_ms"])

    # Redundancy Resolution: Use ws_url as override to region-based derivation
    default_v3_url = "wss://streaming.assemblyai.com/v3/ws"
    if aai_core.ws_url != default_v3_url:
        aai_url = aai_core.ws_url
    else:
        aai_url = default_v3_url
        if aai_core.region == "eu":
            aai_url = "wss://streaming.eu.assemblyai.com/v3/ws"

    # Append mandatory query parameters for V3
    from urllib.parse import urlencode

    params: dict[str, Any] = {}
    if "?" not in aai_url:
        params["sample_rate"] = config.audio.capture_sample_rate
        params["encoding"] = "pcm_s16le"

    params["speech_model"] = aai_core.speech_model

    if aai_adv.keyterms_prompt:
        import json

        params["keyterms_prompt"] = json.dumps(aai_adv.keyterms_prompt)

    if aai_core.language_code != "en":
        params["language_code"] = aai_core.language_code

    if aai_adv.format_text:
        params["format_turns"] = "true"

    if aai_adv.language_detection:
        params["language_detection"] = "true"

    params["vad_threshold"] = str(aai_core.vad_threshold)

    if aai_core.inactivity_timeout_seconds > 0:
        params["inactivity_timeout"] = str(aai_core.inactivity_timeout_seconds)

    # Turn detection overrides or profile values
    params["end_of_turn_confidence_threshold"] = str(aai_confidence)
    params["min_end_of_turn_silence_when_confident"] = str(aai_min_silence)
    params["max_turn_silence"] = str(aai_max_silence)

    if params:
        separator = "&" if "?" in aai_url else "?"
        aai_url = f"{aai_url}{separator}{urlencode(params)}"

    if config.test.enabled:
        aai_url = config.test.assemblyai_mock_url

    # Wrap inactivity timeout calculation to avoid line length issue
    timeout = aai_core.inactivity_timeout_seconds
    resolved_timeout = timeout if timeout > 0 else None

    resolved_aai = EffectiveAssemblyAIConfig(
        url=aai_url,
        sample_rate=config.audio.capture_sample_rate,
        encoding="pcm_s16le",
        speech_model=aai_core.speech_model,
        language_code=aai_core.language_code,
        vad_threshold=aai_core.vad_threshold,
        confidence_threshold=aai_confidence,
        min_silence_ms=aai_min_silence,
        max_silence_ms=aai_max_silence,
        inactivity_timeout=resolved_timeout,
        word_boost=aai_adv.keyterms_prompt if aai_adv.keyterms_prompt else None,
        format_text=aai_adv.format_text,
        language_detection=aai_adv.language_detection,
        is_test=config.test.enabled,
    )

    # 4. Final Assemblage
    return EffectiveConfig(
        provider_type=trans.provider,
        capture_sample_rate=config.audio.capture_sample_rate,
        chunk_ms=config.audio.chunk_ms,
        hotkey=config.hotkeys.hotkey,
        hold_mode=config.hotkeys.hold_mode,
        openai=resolved_openai,
        assemblyai=resolved_aai,
    )
