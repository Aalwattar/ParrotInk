# Implementation Plan: Configuration Refactor & API Alignment

Overhaul the application configuration to use high-level "User Profiles" and ensure strict compliance with the latest OpenAI and AssemblyAI API specifications.

## Phase 1: Configuration Schema Overhaul
Goal: Redefine the Pydantic models and implement the profile-to-value mapping logic.

- [ ] Task: Update `engine/config.py` with the new schema.
    - [ ] Sub-task: Define `LatencyProfile` and `MicProfile` enums/literals.
    - [ ] Sub-task: Implement the mapping logic (Profiles -> Raw Values) within the Config models.
    - [ ] Sub-task: Clean up redundant fields (`[transcription].sample_rate`).
- [ ] Task: Update `migrate_config_file` to handle the structural changes.
- [ ] Task: Write tests for the new configuration logic.
- [ ] Task: Conductor - User Manual Verification 'Configuration Schema Overhaul' (Protocol in workflow.md)

## Phase 2: OpenAI Provider Alignment
Goal: Fix API compliance issues and integrate the new profiles.

- [ ] Task: Refactor `OpenAIProvider._update_session`.
    - [ ] Sub-task: Remove `session.type`.
    - [ ] Sub-task: Implement `mic_profile` -> `noise_reduction` mapping.
    - [ ] Sub-task: Implement `latency_profile` -> `VAD` mapping (with override support).
- [ ] Task: Update OpenAI connection URL logic to include the model parameter.
- [ ] Task: Verify OpenAI transcription with the new 24kHz/pcm16 settings.
- [ ] Task: Conductor - User Manual Verification 'OpenAI Provider Alignment' (Protocol in workflow.md)

## Phase 3: AssemblyAI Provider Alignment
Goal: Fix legacy parameters, add region support, and integrate profiles.

- [ ] Task: Refactor `AssemblyAIProvider._build_url`.
    - [ ] Sub-task: Remove `utterance_silence_threshold_ms`.
    - [ ] Sub-task: Implement `region` -> `WS_URL` mapping.
    - [ ] Sub-task: Implement `latency_profile` -> `Turn Detection` mapping (with override support).
- [ ] Task: Map `format_text` to `format_turns` correctly.
- [ ] Task: Verify AssemblyAI V3 connectivity and turn behavior.
- [ ] Task: Conductor - User Manual Verification 'AssemblyAI Provider Alignment' (Protocol in workflow.md)

## Phase 4: Final Validation & DOD
Goal: Ensure system-wide stability and adherence to standards.

- [ ] Task: Run full test suite (`uv run pytest`).
- [ ] Task: Verify no hardcoded names or absolute paths remain.
- [ ] Task: Pass DOD Gate (Ruff, Mypy).
- [ ] Task: Conductor - User Manual Verification 'Final Validation & DOD' (Protocol in workflow.md)
