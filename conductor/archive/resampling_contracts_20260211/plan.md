# Implementation Plan: Explicit Provider Audio Contracts & Resampling (Track 2)

## Phase 1: Resampling & PCM16 Utilities
Add resampling capabilities and format conversion logic.

- [x] Task: Add `python-soxr` to project dependencies
    - [x] Run `uv add soxr`.
- [x] Task: Implement PCM16 Conversion & Clipping (Red Phase)
    - [x] Create tests in `tests/test_audio_conversion.py`.
    - [x] Implement `scale_and_clip_to_int16` in `engine/audio/processing.py`.
- [x] Task: Implement Stateful Resampler (Red/Green Phase)
    - [x] Create `tests/test_resampler.py`.
    - [x] Implement `Resampler` class wrapping `soxr`.
- [x] Task: Conductor - User Manual Verification 'Conversion & Resampling' (Protocol in workflow.md)

## Phase 2: Audio Adapter Implementation
Implement the adapter that handles provider-specific contracts.

- [x] Task: Define `ProviderAudioSpec` and `AudioAdapter` (Red Phase)
    - [x] Create tests in `tests/test_audio_adapter.py`.
- [x] Task: Implement `AudioAdapter` (Green Phase)
    - [x] Implement `AudioAdapter` in `engine/audio/adapter.py`.
    - [x] Logic: PCM16 conversion -> Resample -> Encode -> Frame.
- [x] Task: Conductor - User Manual Verification 'Audio Adapter' (Protocol in workflow.md)

## Phase 3: Provider Refactoring & Integration
Update providers and integrate.

- [x] Task: Refactor Providers
    - [x] Update OpenAI and AssemblyAI providers to use the adapter.
- [x] Task: Update `AppCoordinator` Integration
    - [x] Initialize `AudioAdapter` based on active provider.
- [x] Task: Final "Done" Gate Verification
    - [x] Run `uv run ruff check .`
    - [x] Run `uv run ruff format --check .`
    - [x] Run `uv run mypy .`
    - [x] Run `uv run pytest -q`
- [x] Task: Conductor - User Manual Verification 'Provider Integration' (Protocol in workflow.md)
