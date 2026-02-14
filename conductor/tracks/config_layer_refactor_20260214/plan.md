# Implementation Plan: Configuration Layer Refactor (EffectiveConfig)

Introduce a formal separation between the user-facing TOML configuration and the internal, validated `EffectiveConfig` state using a staged resolution pipeline.

## Phase 1: Foundation & UserConfig Schema
Goal: Define the raw TOML schema and the orchestrator structure.

- [ ] Task: Define `UserConfig` Pydantic models in `engine/config.py`.
    - [ ] Sub-task: Create models that strictly match the TOML structure (profiles, raw values).
- [ ] Task: Create `engine/config_resolver.py`.
    - [ ] Sub-task: Implement `ConfigResolver` orchestrator class.
    - [ ] Sub-task: Implement basic TOML parsing and migration hook.
- [ ] Task: Conductor - User Manual Verification 'Foundation & UserConfig Schema' (Protocol in workflow.md)

## Phase 2: EffectiveConfig & Specialized Compilers
Goal: Implement the logic to derive precise engineering values from user profiles.

- [ ] Task: Define `EffectiveConfig` and its immutable sub-blocks (`CompiledAudioSettings`, etc.).
- [ ] Task: Implement `compile_audio` logic.
    - [ ] Sub-task: Resolve capture rate and resample targets.
- [ ] Task: Implement `compile_ui` and `compile_interaction` logic.
- [ ] Task: Implement provider compilers (`compile_openai`, `compile_assemblyai`).
    - [ ] Sub-task: Map `latency_profile` to VAD/Turn-detection timings.
    - [ ] Sub-task: Map `mic_profile` to Noise Reduction enums.
    - [ ] Sub-task: Implement `override` logic (if `override=true`, use raw values).
- [ ] Task: Implement cross-field invariant validation (e.g., timeout ranges).
- [ ] Task: Conductor - User Manual Verification 'EffectiveConfig & Specialized Compilers' (Protocol in workflow.md)

## Phase 3: Engine Integration (Constructor Injection)
Goal: Refactor the application to consume compiled settings instead of raw config.

- [ ] Task: Update `main.py` to use `ConfigResolver` at startup.
- [ ] Task: Refactor `AudioEngine` to accept `CompiledAudioSettings`.
- [ ] Task: Refactor `OpenAIProvider` and `AssemblyAIProvider` to accept their respective compiled settings.
    - [ ] Sub-task: Remove all profile mapping logic from provider modules.
- [ ] Task: Refactor UI and Interaction modules.
- [ ] Task: Conductor - User Manual Verification 'Engine Integration (Constructor Injection)' (Protocol in workflow.md)

## Phase 4: Diagnostics & CLI Tools
Goal: Implement the `--explain` command and finalize security.

- [ ] Task: Implement `app config --explain`.
    - [ ] Sub-task: Display resolution logic (Profiles -> Raw values).
    - [ ] Sub-task: Implement mandatory secrets redaction for all config output.
- [ ] Task: Integrate with existing `-v`/`--verbose` flag for detailed payload previews.
- [ ] Task: Generate/Update `config.example.toml` with derived guidance comments.
- [ ] Task: Conductor - User Manual Verification 'Diagnostics & CLI Tools' (Protocol in workflow.md)

## Phase 5: Verification & DOD
Goal: Ensure zero regressions and pass all project quality gates.

- [ ] Task: Write comprehensive unit tests for the Resolver and Compilers.
- [ ] Task: Run full test suite (`uv run pytest`).
- [ ] Task: Pass DOD Gate (Ruff, Mypy).
- [ ] Task: Conductor - User Manual Verification 'Verification & DOD' (Protocol in workflow.md)
