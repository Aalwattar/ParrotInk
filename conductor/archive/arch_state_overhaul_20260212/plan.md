# Implementation Plan: Architecture & State Overhaul

Refactor the application core to use a unified state machine and specialized controllers.

## Phase 1: State Machine Foundation (I2)
Goal: Centralize state management to eliminate race conditions.

- [x] Task: Update `AppState` in `engine/app_types.py` with expanded states: `IDLE`, `CONNECTING`, `LISTENING`, `STOPPING`, `ERROR`, `SHUTTING_DOWN`.
- [x] Task: Refactor `AppCoordinator` to use `self.state` instead of individual booleans.
- [x] Task: Implement transition logic (e.g., `set_state()` method) that handles associated side effects.
- [x] Task: Update UI components and tests to reflect the new state enum.
- [x] Task: Conductor - User Manual Verification 'State Machine'

## Phase 2: Connection Management (I1)
Goal: Extract connection and provider lifecycle logic.

- [x] Task: Create `engine/connection.py` containing a `ConnectionManager` class.
- [x] Task: Move provider creation, `ensure_connected`, warm-connection timers, and rotation logic into `ConnectionManager`.
- [x] Task: Integrate `ConnectionManager` into `AppCoordinator`.
- [x] Task: Write unit tests for `ConnectionManager` lifecycle.
- [x] Task: Conductor - User Manual Verification 'Connection Manager'

## Phase 3: Audio Pipeline Extraction (I1)
Goal: Isolate the audio streaming and processing loop.

- [x] Task: Create `engine/audio/pipeline.py` containing an `AudioPipeline` class.
- [x] Task: Move the `_audio_pipe` task logic and `AudioStreamer`/`AudioAdapter` management into this class.
- [x] Task: Implement strict start/stop invariants in the pipeline.
- [x] Task: Integrate `AudioPipeline` into `AppCoordinator`.
- [x] Task: Conductor - User Manual Verification 'Audio Pipeline'

## Phase 4: Final Decoupling & Cleanup
Goal: Slim down `AppCoordinator` and ensure strict separation of concerns.

- [x] Task: Move remaining injection logic to a dedicated `InjectionController`.
- [x] Task: Final project-wide audit for "leaked" logic (e.g., UI calls inside managers).
- [x] Task: Pass DOD Gate:
    - [x] `uv run ruff check .`
    - [x] `uv run ruff format .`
    - [x] `uv run mypy .`
    - [x] `uv run pytest`
- [x] Task: Conductor - User Manual Verification 'Architecture Overhaul Finalization'
