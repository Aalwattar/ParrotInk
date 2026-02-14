# Implementation Plan: Configuration System Overhaul

Overhaul the configuration system to support staged resolution, strict API alignment, and diagnostic tools.

## Phase 1: Architecture & UserConfig Schema
Goal: Define the staged pipeline and the raw TOML mapping.

- [ ] Task: Create `engine/config_resolver.py` and define `UserConfig`.
    - [ ] Sub-task: Create Pydantic models matching the simplified TOML structure.
    - [ ] Sub-task: Implement `ConfigResolver.parse()` with migration hooks.
- [ ] Task: Remove redundant fields from `engine/config.py`.
    - [ ] Sub-task: Drop `[transcription].sample_rate` and redundant `language` keys.
- [ ] Task: Conductor - User Manual Verification 'Architecture & UserConfig Schema' (Protocol in workflow.md)

## Phase 2: EffectiveConfig & Specialized Compilers
Goal: Implement mapping logic for profiles and validation.

- [ ] Task: Define `EffectiveConfig` and its immutable sub-blocks.
- [ ] Task: Implement `compile_audio`, `compile_ui`, and `compile_interaction`.
- [ ] Task: Implement provider compilers (`compile_openai`, `compile_assemblyai`).
    - [ ] Sub-task: Map `latency_profile` to VAD/Turn-detection timings.
    - [ ] Sub-task: Map `mic_profile` to OpenAI Noise Reduction enums.
    - [ ] Sub-task: Implement `override` logic.
- [ ] Task: Implement strict invariant validation (Fail Fast).
- [ ] Task: Conductor - User Manual Verification 'EffectiveConfig & Specialized Compilers' (Protocol in workflow.md)

## Phase 3: OpenAI Provider Alignment
Goal: Align with Realtime Transcription sessions and 24k rate.

- [ ] Task: Refactor `OpenAIProvider`.
    - [ ] Sub-task: Update `_update_session` to use `session.type = "transcription"`.
    - [ ] Sub-task: Enforce `audio/pcm` @ 24k on-wire.
    - [ ] Sub-task: Separate `realtime_model` from `transcription_model`.
- [ ] Task: Update `AudioAdapter` to support resampling to 24k for OpenAI.
- [ ] Task: Conductor - User Manual Verification 'OpenAI Provider Alignment' (Protocol in workflow.md)

## Phase 4: AssemblyAI Provider Alignment
Goal: Align with Streaming V3 and regional endpoints.

- [ ] Task: Refactor `AssemblyAIProvider`.
    - [ ] Sub-task: Update `_build_url` for US/EU regions and remove legacy params.
    - [ ] Sub-task: Map `format_text` to `format_turns`.
- [ ] Task: Verify chunk timing (50ms-1000ms).
- [ ] Task: Conductor - User Manual Verification 'AssemblyAI Provider Alignment' (Protocol in workflow.md)

## Phase 5: Diagnostics, CLI Tools & DOD
Goal: Implement `--explain` and finalize project gates.

- [ ] Task: Implement `app config --explain`.
    - [ ] Sub-task: Show mapping logic and redacted settings.
    - [ ] Sub-task: Support `-v` for payload previews.
- [ ] Task: Update `main.py` entry point to use `ConfigResolver` and Constructor Injection.
- [ ] Task: Pass DOD Gate (Ruff, Mypy, Pytest).
- [ ] Task: Conductor - User Manual Verification 'Diagnostics, CLI Tools & DOD' (Protocol in workflow.md)
