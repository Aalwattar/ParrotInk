# Specification: Unified Configuration & OpenAI Dialect Alignment

## 1. Overview
This track finalizes the configuration architecture of ParrotInk. It resolves technical inconsistencies in the OpenAI Realtime implementation by standardizing on "Dialect B" (Transcription-only), purges legacy AssemblyAI parameters, and enforces a "Basic vs. Advanced" configuration template strategy. It ensures the application is locked to Transcription-only mode for OpenAI, preventing accidental usage of conversational models.

## 2. Core Invariants & Dialect Selection
- **OpenAI Dialect:** The application MUST use **Dialect B** (`transcription_session.update`).
- **OpenAI Mode:** Strictly **Transcription-only**. No voice, no output modalities, no responses.
- **AssemblyAI Mode:** Streaming V3 only. No legacy V2 parameters.

## 3. Configuration Schema Refinement (`engine/config.py`)

### 3.1 Global `[transcription]` Section
- **Remove:** `language`. (Language is now provider-local).
- **Keep:** `provider` (Single selector), `latency_profile`, `mic_profile`, `format_text`.

### 3.2 OpenAI `[providers.openai.core]` Section
- **Remove:** `realtime_model`. (Redundant for transcription-only sessions).
- **Remove:** `input_audio_rate`, `input_audio_type`. (These are now engine constants).
- **Add:** `language: str = "en"`.
- **Validation:** Add a Pydantic validator to `transcription_model`. It MUST reject any model starting with `gpt-realtime`. Only `gpt-4o-mini-transcribe` or `gpt-4o-transcribe` family models are allowed.

### 3.3 AssemblyAI `[providers.assemblyai.core]` Section
- **Remove:** `encoding`, `sample_rate`. (These must match capture rate or be fixed).
- **Remove:** `utterance_silence_threshold_ms`. (Not supported in V3).
- **Keep:** `speech_model`, `language_detection`, `region`, and `ws_url` (optional override).

## 4. Technical Logic Implementation

### 4.1 OpenAI Provider (`OpenAIProvider`)
- **Connection:** WebSocket URL MUST include `?intent=transcription`.
- **Constants:** Define `OPENAI_TRANSCRIPTION_SCHEMA = "B"`.
- **Format Invariants:** Hardcode `input_audio_format = "pcm16"` (implies 24kHz mono PCM16).
- **Resampling:** Ensure the engine always resamples to 24kHz before sending.
- **Update Event:** Use `type: "transcription_session.update"`.
    - Payload structure (Flat fields, no wrapper):
      ```json
      {
        "type": "transcription_session.update",
        "input_audio_format": "pcm16",
        "input_audio_transcription": { "model": "gpt-4o-mini-transcribe", "language": "en", "prompt": "" },
        "turn_detection": { "type": "server_vad", "threshold": 0.5, "prefix_padding_ms": 300, "silence_duration_ms": 500 },
        "input_audio_noise_reduction": { "type": "near_field" }
      }
      ```
- **Logging:** Under `-vv`, log event type (`delta` vs `completed`), text length, and timestamp for all server messages.

### 4.2 AssemblyAI Provider (`AssemblyAIProvider`)
- **Format Invariants:** Hardcode `encoding = "pcm_s16le"`.
- **Dynamic Rate:** The `sample_rate` parameter MUST be set to match `audio.capture_sample_rate` dynamically.
- **URL Resolution:** Endpoint derived from `region` (US/EU) unless a custom `ws_url` override is provided.

### 4.3 Config Resolver (`engine/config_resolver.py`)
- Update the resolver to populate the `EffectiveConfig` snapshots based on the new local language settings.
- Ensure all invariants (24k for OpenAI, dynamic for AAI) are calculated here.

## 5. Configuration Presentation (`config.example.toml`)
Implement a **Basic vs. Advanced** strategy:
- **Basic:** Provider, Hotkey, Toggle Mode, Sounds/HUD enabled.
- **Advanced (Commented Out):** Models, VAD thresholds, Region, URLs.
- **Warnings:** Add clear header comments:
    - "NOTE: OpenAI is for Transcription Mode only. Speech-to-Speech is not supported."
    - "Do not modify advanced values unless you have specific hardware requirements."

## 6. Acceptance Criteria
- [ ] OpenAI connects with `?intent=transcription`.
- [ ] OpenAI uses `transcription_session.update` with Dialect B schema.
- [ ] Attempting to set a `gpt-realtime` model results in a `ConfigError`.
- [ ] AssemblyAI V3 works without `utterance_silence_threshold_ms`.
- [ ] Changing `capture_sample_rate` to 44100 (if hardware supported) correctly updates AssemblyAI's wire rate while OpenAI remains resampled to 24k.
- [ ] `app config --explain` shows the correct Dialect B structure for OpenAI.
- [ ] `config.example.toml` is cleanly separated and commented.
