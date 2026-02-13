# Implementation Plan: Architecture & State Overhaul

Refactor the application core to use a unified state machine and specialized controllers.

## Phase 1: State Machine Foundation (I2)
Goal: Centralize state management to eliminate race conditions.

- [ ] Task: Update `AppState` in `engine/app_types.py` with expanded states: `IDLE`, `CONNECTING`, `LISTENING`, `STOPPING`, `ERROR`, `SHUTTING_DOWN`.
- [ ] Task: Refactor `AppCoordinator` to use `self.state` instead of individual booleans.
- [ ] Task: Implement transition logic (e.g., `set_state()` method) that handles associated side effects.
- [ ] Task: Update UI components and tests to reflect the new state enum.
- [ ] Task: Conductor - User Manual Verification 'State Machine'

## Phase 2: Connection Management (I1)
Goal: Extract connection and provider lifecycle logic.

- [ ] Task: Create `engine/connection.py` containing a `ConnectionManager` class.
- [ ] Task: Move provider creation, `ensure_connected`, warm-connection timers, and rotation logic into `ConnectionManager`.
- [ ] Task: Integrate `ConnectionManager` into `AppCoordinator`.
- [ ] Task: Write unit tests for `ConnectionManager` lifecycle.
- [ ] Task: Conductor - User Manual Verification 'Connection Manager'

## Phase 3: Audio Pipeline Extraction (I1)
Goal: Isolate the audio streaming and processing loop.

- [ ] Task: Create `engine/audio/pipeline.py` containing an `AudioPipeline` class.
- [ ] Task: Move the `_audio_pipe` task logic and `AudioStreamer`/`AudioAdapter` management into this class.
- [ ] Task: Implement strict start/stop invariants in the pipeline.
- [ ] Task: Integrate `AudioPipeline` into `AppCoordinator`.
- [ ] Task: Conductor - User Manual Verification 'Audio Pipeline'

## Phase 4: Final Decoupling & Cleanup
Goal: Slim down `AppCoordinator` and ensure strict separation of concerns.

- [ ] Task: Move remaining injection logic to a dedicated `InjectionController`.
- [ ] Task: Final project-wide audit for "leaked" logic (e.g., UI calls inside managers).
- [ ] Task: Pass DOD Gate:
    - [ ] `uv run ruff check .`
    - [ ] `uv run ruff format .`
    - [ ] `uv run mypy .`
    - [ ] `uv run pytest`
- [ ] Task: Conductor - User Manual Verification 'Architecture Overhaul Finalization'
