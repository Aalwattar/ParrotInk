# Implementation Plan: Shutdown Orchestration (Track 3)

## Phase 1: Shutdown Core & Signal Handling
Implement the base shutdown logic and wire up OS signals.

- [x] Task: Create unit tests for idempotent shutdown (Red Phase)
    - [x] Create `tests/test_shutdown_logic.py`.
    - [x] Verify `shutdown()` only runs once despite multiple calls.
    - [x] Verify shutdown order using mocks/spies.
- [x] Task: Implement `AppCoordinator.shutdown()` (Green Phase)
    - [x] Add `_shutdown_lock` and `_is_shutting_down` flag.
    - [x] Implement the ordered cleanup steps with `asyncio.timeout(2.0)`.
- [x] Task: Implement Signal Handling
    - [x] Update `main.py` entry point to register `SIGINT` and `SIGTERM` handlers.
    - [x] Ensure handlers call `shutdown()` via `loop.create_task` or similar.
- [x] Task: Conductor - User Manual Verification 'Shutdown Core' (Protocol in workflow.md)

## Phase 2: UI & Thread Synchronization
Ensure the UI thread and audio threads are cleanly joined.

- [x] Task: Improve UI Bridge for Shutdown
    - [x] Ensure `UIBridge` can trigger the `shutdown()` flow from the tray "Exit" menu.
    - [x] Verify `pystray` icon stop and thread join logic.
- [x] Task: Implement Total Shutdown Deadline
    - [x] Wrap the entire shutdown sequence in a global timeout (10s).
    - [x] Implement the `os._exit(1)` fallback for timed-out shutdowns.
- [x] Task: Refactor and Verify Coverage
    - [x] Verify >80% coverage for the shutdown-related logic.
- [x] Task: Conductor - User Manual Verification 'UI & Thread Joining' (Protocol in workflow.md)

## Phase 3: Regression Testing & Smoke Tests
Verify end-to-end shutdown behavior under various conditions.

- [x] Task: Create Smoke Test for Clean Exit
    - [x] Update `tests/smoke_main.py` or create a new exit-specific test.
    - [x] Test shutdown via Ctrl+C.
    - [x] Test shutdown via simulated UI exit.
- [x] Task: Final "Done" Gate Verification
    - [x] Run `uv run ruff check .`
    - [x] Run `uv run ruff format --check .`
    - [x] Run `uv run mypy .`
    - [x] Run `uv run pytest -q`
- [x] Task: Conductor - User Manual Verification 'End-to-End Shutdown' (Protocol in workflow.md)
