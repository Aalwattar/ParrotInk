from typing import Any, Literal, Optional

from .app_types import (
    EffectiveAssemblyAIConfig,
    EffectiveCloudflareConfig,
    EffectiveConfig,
    EffectiveOpenAIConfig,
)
from .config import LATENCY_PROFILES, MIC_PROFILES, Config
from .logging import get_logger

logger = get_logger("ConfigResolver")


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
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

    def with_params(url: str, parameters: dict) -> str:
        parsed = urlsplit(url)
        query = dict(parse_qsl(parsed.query))
        query.update(parameters)
        return urlunsplit(parsed._replace(query=urlencode(query)))

    openai_url = with_params(openai_core.realtime_ws_url_base, {"intent": "transcription"})
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
        stop_timeout=config.audio.provider_stop_timeout_seconds,
        is_test=config.test.enabled,
        languages=tuple(
            openai_core.languages or ([openai_core.language] if openai_core.language else [])
        ),
        keywords=tuple(openai_adv.keywords),
        delay=openai_adv.delay
        if openai_adv.override
        else {"fast": "low", "balanced": "medium", "accurate": "high"}[trans.latency_profile],
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
    from .transcription.catalog import get_model

    aai_model = get_model("assemblyai", aai_core.speech_model)
    params: dict[str, Any] = {
        "sample_rate": config.audio.capture_sample_rate,
        "encoding": "pcm_s16le",
    }

    params["speech_model"] = aai_core.speech_model

    # Priority Logic: prompt vs keyterms_prompt (mutual exclusivity)
    if aai_core.prompt:
        params["prompt"] = aai_core.prompt
        if aai_adv.keyterms_prompt and not aai_model.modern:
            logger.warning(
                "Both 'prompt' and 'keyterms_prompt' provided for AssemblyAI. "
                "'prompt' takes precedence; 'keyterms_prompt' ignored."
            )
    if aai_adv.keyterms_prompt and (not aai_core.prompt or aai_model.modern):
        import json

        params["keyterms_prompt"] = json.dumps(aai_adv.keyterms_prompt)

    # Language Handling: Auto-detection vs Manual ISO code
    if aai_model.modern:
        import json

        codes = aai_core.language_codes or (
            [aai_core.language_code] if aai_core.language_code else []
        )
        if codes:
            params["language_codes"] = json.dumps(codes)
    elif not aai_core.language_code:
        # If language is empty, enable auto-detection for supported models.
        # Universal-3 Pro and U3 Multilingual support this on V3.
        if aai_core.speech_model in ("u3-rt-pro", "universal-streaming-multilingual", "whisper-rt"):
            params["language_detection"] = "true"
        elif aai_core.speech_model == "universal-3-5-pro":
            # For Universal-3.5 Pro, leaving language_code off enables
            # native multi-language code-switching. So we do not set
            # language_detection or language_code.
            pass
        else:
            # Fallback for English-only model (universal-streaming-english)
            params["language_code"] = "en"
    else:
        params["language_code"] = aai_core.language_code

    if aai_adv.format_text and not aai_model.modern:
        params["format_turns"] = "true"

    if aai_adv.enable_diarization:
        params["speaker_labels"] = "true"

    if not aai_model.modern or aai_adv.override:
        params["vad_threshold"] = str(aai_core.vad_threshold)

    if aai_core.inactivity_timeout_seconds > 0:
        params["inactivity_timeout"] = str(aai_core.inactivity_timeout_seconds)

    # Turn detection overrides or profile values
    if not aai_model.modern or aai_adv.override:
        params["min_turn_silence"] = str(aai_min_silence)
        params["max_turn_silence"] = str(aai_max_silence)
    if not aai_model.modern:
        params["end_of_turn_confidence_threshold"] = str(aai_confidence)

    # Resolve voice_focus and mode (prioritize core override over shared profiles)
    resolved_mode: Literal["balanced", "min_latency", "max_accuracy"] = aai_core.mode
    resolved_voice_focus: Optional[str] = None
    if aai_model.modern:
        if aai_adv.override:
            resolved_mode = aai_core.mode
        else:
            latency_map: dict[str, Literal["balanced", "min_latency", "max_accuracy"]] = {
                "fast": "min_latency",
                "balanced": "balanced",
                "accurate": "max_accuracy",
            }
            resolved_mode = latency_map.get(trans.latency_profile, "balanced")

        if aai_core.voice_focus:
            resolved_voice_focus = aai_core.voice_focus
        else:
            focus = MIC_PROFILES.get(trans.mic_profile)
            resolved_voice_focus = focus.replace("_", "-") if focus else None

    # Append new streaming parameters if using the new model (or u3-rt-pro)
    if aai_model.modern:
        params["mode"] = resolved_mode
        if aai_core.agent_context:
            params["agent_context"] = aai_core.agent_context[:1500]
        if resolved_voice_focus:
            params["voice_focus"] = resolved_voice_focus

    # Update URL with resolved parameters
    aai_url = with_params(aai_url, params)

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
        prompt=aai_core.prompt,
        language_code=aai_core.language_code,
        vad_threshold=aai_core.vad_threshold,
        confidence_threshold=aai_confidence,
        min_silence_ms=aai_min_silence,
        max_silence_ms=aai_max_silence,
        inactivity_timeout=resolved_timeout,
        format_text=aai_adv.format_text,
        enable_diarization=aai_adv.enable_diarization,
        stop_timeout=config.audio.provider_stop_timeout_seconds,
        is_test=config.test.enabled,
        mode=resolved_mode,
        agent_context=aai_core.agent_context,
        voice_focus=resolved_voice_focus,
    )

    # Gateway is a route to a selected model, whose wire protocol stays explicit.
    cf_core = config.providers.cloudflare.core
    cf_model = get_model("cloudflare", cf_core.model)
    cf_base = f"wss://gateway.ai.cloudflare.com/v1/{cf_core.account_id}/{cf_core.gateway_id}"
    cf_params: dict[str, Any]
    if cf_model.protocol == "unavailable":
        cf_url = ""
    elif cf_model.protocol == "grok_stt":
        cf_params = {
            "model": cf_core.model,
            "websocket": "true",
            "audio_format": "pcm",
            "sample_rate": config.audio.capture_sample_rate,
        }
        if cf_core.language:
            cf_params["language"] = cf_core.language
            cf_params["format"] = "true"
        cf_url = with_params(
            f"wss://api.cloudflare.com/client/v4/accounts/{cf_core.account_id}/ai/run",
            cf_params,
        )
    else:
        cf_params = {
            "model": cf_core.model,
            "encoding": "linear16",
            "sample_rate": config.audio.capture_sample_rate,
        }
        if cf_model.protocol == "deepgram_nova":
            cf_params.update(
                interim_results="true", endpointing=cf_core.endpointing_ms, smart_format="true"
            )
            if cf_core.language:
                cf_params["language"] = cf_core.language
        cf_url = with_params(f"{cf_base}/workers-ai", cf_params)
    if config.test.enabled:
        cf_url = config.test.cloudflare_mock_url
    resolved_cf = EffectiveCloudflareConfig(
        url=cf_url,
        model=cf_core.model,
        protocol=cf_model.protocol,
        sample_rate=config.audio.capture_sample_rate,
        language=cf_core.language,
        endpointing_ms=cf_core.endpointing_ms,
        stop_timeout=config.audio.provider_stop_timeout_seconds,
        is_test=config.test.enabled,
        gateway_id=cf_core.gateway_id,
    )

    # 4. Final Assemblage
    return EffectiveConfig(
        provider_type=trans.provider,
        capture_sample_rate=config.audio.capture_sample_rate,
        chunk_ms=config.audio.chunk_ms,
        hotkey=config.hotkeys.hotkey,
        hold_mode=config.hotkeys.hold_mode,
        partial_results=config.transcription.partial_results,
        openai=resolved_openai,
        assemblyai=resolved_aai,
        cloudflare=resolved_cf,
    )
