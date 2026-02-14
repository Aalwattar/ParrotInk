# Implementation Plan: Unified Configuration & OpenAI Dialect Alignment

## Phase 1: Schema Refine & Validation
Goal: Modernize the Pydantic schema and enforce local settings.

- [ ] Task: Update `engine/config.py` schema.
    - [ ] Task: Remove `language` from `TranscriptionConfig`.
    - [ ] Task: Add `language` to `OpenAICoreConfig`.
    - [ ] Task: Add model validator to `OpenAICoreConfig` to reject `gpt-realtime*`.
    - [ ] Task: Remove `realtime_model`, `input_audio_rate`, and `input_audio_type` from `OpenAICoreConfig`.
    - [ ] Task: Remove `sample_rate`, `encoding`, and `utterance_silence_threshold_ms` from `AssemblyAICoreConfig`.
- [ ] Task: Update `engine/config_resolver.py`.
    - [ ] Task: Map local languages to `EffectiveConfig` snapshots.
    - [ ] Task: Implement dynamic rate derivation for AssemblyAI.
    - [ ] Task: Implement Dialect B snapshot for OpenAI.
- [ ] Task: Pass DOD Gate (Ruff, Mypy).
- [ ] Task: Conductor - User Manual Verification 'Schema Refine & Validation' (Protocol in workflow.md)

## Phase 2: OpenAI Dialect B Implementation
Goal: Align OpenAI provider with the transcription-only convenience style.

- [ ] Task: Update `engine/transcription/openai_provider.py`.
    - [ ] Task: Update WebSocket URL to strictly include `?intent=transcription`.
    - [ ] Task: Implement `transcription_session.update` client event logic with a **flat schema** (no wrapper).
    - [ ] Task: Enforce Dialect B payload keys (`input_audio_noise_reduction`, etc.; no conversation keys).
    - [ ] Task: Add verbose logging for `delta` and `completed` events under `-vv`.
- [ ] Task: Verify resampling logic.
    - [ ] Task: Confirm `get_audio_spec` returns `24000` and `pcm16_base64`.
- [ ] Task: Add unit test verifying that the outgoing OpenAI payload uses the correct Dialect B keys.
- [ ] Task: Conductor - User Manual Verification 'OpenAI Dialect B Alignment' (Protocol in workflow.md)

## Phase 3: AssemblyAI V3 Cleanup & Invariants
Goal: Purge legacy parameters and stabilize wire protocol.

- [ ] Task: Update `engine/transcription/assemblyai_provider.py`.
    - [ ] Task: Hardcode `encoding` to `pcm_s16le`.
    - [ ] Task: Ensure query params include dynamically resolved `sample_rate`.
    - [ ] Task: Verify that `utterance_silence_threshold` is not sent.
- [ ] Task: Conductor - User Manual Verification 'AssemblyAI V3 Cleanup' (Protocol in workflow.md)

## Phase 4: Final Polishing & Documentation
Goal: Refactor configuration template and diagnostics.

- [ ] Task: Update `explain_config` in `engine/config.py` to reflect the new Dialect B snapshot.
- [ ] Task: Rewrite `config.example.toml`.
    - [ ] Task: Implement Basic vs. Advanced separation.
    - [ ] Task: Comment out advanced keys and add warnings.
- [ ] Task: Final DOD Gate (Ruff, Mypy, Pytest).
- [ ] Task: Conductor - User Manual Verification 'Final Polishing & DOD' (Protocol in workflow.md)
