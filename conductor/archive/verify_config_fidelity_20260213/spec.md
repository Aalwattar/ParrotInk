# Track Specification: Verify Config Fidelity

**Goal:** Eliminate all hardcoded transcription parameters in `AssemblyAIProvider` and `OpenAIProvider`. Ensure all tunable parameters (VAD, silence, thresholds) are exposed via `config.toml`.

## 1. Problem Statement
Recurring issue where configuration knobs (e.g., `min_end_of_turn_silence`) are defined in `config.toml` but ignored in the provider implementation, which uses hardcoded defaults. This prevents tuning and experimentation.

## 2. Scope

### A. AssemblyAI Provider (`engine/transcription/assemblyai_provider.py`)
- **Fix:** Replace hardcoded VAD values in `_build_url` with values from `self.config.providers.assemblyai`.
- **Verify:**
    - `end_of_turn_confidence_threshold`
    - `min_end_of_turn_silence_when_confident`
    - `max_turn_silence`
    - `utterance_silence_threshold`
    - `vad_threshold`
    - `inactivity_timeout`

### B. OpenAI Provider (`engine/transcription/openai_provider.py`)
- **Audit:** Confirm `session.update` correctly maps all `core` and `advanced` config fields.
- **Fix:** If any field is missing or hardcoded, map it.

### C. Config Schema (`engine/config.py`)
- **Audit:** Ensure the `pydantic` models actually support the fields we need.

## 3. Success Criteria
- [ ] No integer literals for VAD/timing params in provider files.
- [ ] All parameters are sourced from `self.config`.
- [ ] Tests pass.
