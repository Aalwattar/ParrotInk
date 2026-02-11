# Implementation Plan: Audio Pipeline Optimization (Track 1)

## Phase 1: Capture Boundary Invariants
This phase focuses on the "cheap and universal" logic for processing raw audio chunks at the capture boundary.

- [x] Task: Create unit tests for capture boundary logic (Red Phase)
    - [x] Create `tests/test_audio_boundary.py`.
    - [x] Add tests for `downmix_stereo_to_mono`.
    - [x] Add tests for `reshape_to_1d`.
    - [x] Add tests for `sanitize_nan_inf`.
    - [x] Add tests for rejecting `ndim > 2`.
- [x] Task: Implement boundary invariants (Green Phase)
    - [x] Define `CaptureFormatError` in `engine/types.py`.
    - [x] Implement processing functions in `engine/audio.py`.
    - [x] Ensure all tests in `tests/test_audio_boundary.py` pass.
- [x] Task: Refactor and Verify Coverage
    - [x] Verify >80% coverage for `engine/audio.py`.
- [x] Task: Conductor - User Manual Verification 'Capture Boundary' (Protocol in workflow.md)

## Phase 2: Event-Driven Streamer Implementation
Replace the polling-based `AudioStreamer` with an `asyncio.Queue`.

- [x] Task: Create integration tests for `AudioStreamer` queue logic (Red Phase)
    - [x] Create `tests/test_audio_streamer_async.py`.
    - [x] Test "Drop Oldest" overflow behavior.
- [x] Task: Implement `asyncio.Queue` in `AudioStreamer` (Green Phase)
    - [x] Update `AudioStreamer` to use `asyncio.Queue(maxsize=100)`.
    - [x] Integrate invariant utilities into the `sounddevice` callback via `call_soon_threadsafe`.
- [x] Task: Implement Resilience & Error Handling
    - [x] Add failure counters and rate-limited logging for loop errors.
    - [x] Implement the `stop_capture` threshold logic.
- [x] Task: Refactor and Verify Coverage
    - [x] Ensure `AudioStreamer` is clean and adheres to style guides.
- [x] Task: Conductor - User Manual Verification 'Event-Driven Streamer' (Protocol in workflow.md)

## Phase 3: System Integration & Smoke Testing
Integrate and verify end-to-end functionality.

- [x] Task: Update `AppCoordinator` Integration
    - [x] Remove polling/sleep logic.
- [x] Task: Final "Done" Gate Verification
    - [x] Run `uv run ruff check .`
    - [x] Run `uv run ruff format --check .`
    - [x] Run `uv run mypy .`
    - [x] Run `uv run pytest -q`
- [x] Task: Conductor - User Manual Verification 'System Integration' (Protocol in workflow.md)
