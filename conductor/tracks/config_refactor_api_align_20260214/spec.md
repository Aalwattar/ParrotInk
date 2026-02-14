# Specification: Configuration Refactor & API Alignment

Overhaul the application configuration to use high-level "User Profiles" and ensure strict compliance with the latest OpenAI and AssemblyAI API specifications.

## 1. Overview
The current configuration is "messy," exposing low-level engineering parameters to users and containing several legacy or incorrect API keys. This track will:
1.  **Simplify Config:** Introduce `latency_profile` and `mic_profile` to hide complex VAD/NR values.
2.  **Align APIs:** Fix known bugs in OpenAI (`session.type` removal, 24k rate enforcement) and AssemblyAI (V3 turn detection presets, region support).
3.  **Standardize Structure:** Centralize global transcription settings and remove redundancies.

## 2. Functional Requirements

### 2.1. User-First Configuration Schema
- **Latency Profiles:** Implement `fast`, `balanced`, and `accurate` profiles.
- **Mic Profiles:** Implement `headset`, `laptop`, and `none` profiles.
- **Global Transcription Block:** Move `provider`, `language`, and profiles to a top-level `[transcription]` block.
- **Redundancy Removal:** Remove `[transcription].sample_rate`. Centralize on `[audio].capture_sample_rate`.

### 2.2. OpenAI Alignment (Realtime API)
- **API Fixes:**
    - Remove `session.type` from `session.update`.
    - Hard-code `audio/pcm` at `24000` rate in the payload.
    - Map `mic_profile` to `noise_reduction` (`near_field`, `far_field`, or `null`).
- **Profile Mapping:** Map `latency_profile` to `vad_threshold` and `silence_duration_ms`.

### 2.3. AssemblyAI Alignment (Streaming V3)
- **API Fixes:**
    - Remove legacy `utterance_silence_threshold_ms`.
    - Implement `region` selection (`us` vs `eu`) with corresponding WebSocket URLs.
    - Implement `format_text` (mapping to `format_turns`).
- **Profile Mapping:** Map `latency_profile` to AssemblyAI's documented `Aggressive`, `Balanced`, and `Conservative` triples.

### 2.4. Power User Overrides
- Add an `override = false` flag to `[providers.*.advanced]` blocks. 
- If `true`, the provider ignores the high-level `latency_profile` and uses the raw numbers.

## 3. Technical Constraints
- **Pydantic Validation:** Update `engine/config.py` models to enforce the new schema.
- **Resampling Integrity:** Ensure the `AudioAdapter` or Providers correctly handle the 16k -> 24k resampling for OpenAI.
- **Backward Compatibility:** Provide a migration path or sensible defaults so existing `config.toml` files don't break the app.

## 4. Acceptance Criteria
- [ ] `config.toml` uses the simplified profile-based structure.
- [ ] OpenAI connection no longer triggers "Unknown parameter: session.type" errors.
- [ ] AssemblyAI connection uses correct regional endpoints.
- [ ] Changing `latency_profile` correctly updates internal VAD/Turn-detection timings.
- [ ] All tests (especially configuration and provider tests) pass.

## 5. Out of Scope
- Adding local Digital Signal Processing (DSP) libraries.
- Changing the primary TOML format to JSON or YAML.
