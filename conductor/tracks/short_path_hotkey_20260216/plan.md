# Implementation Plan: Short Path Hotkey Migration

This track simplifies the hotkey architecture and implements selective suppression using the `keyboard` library.

## Phase 1: Infrastructure & Cleanup
- [x] Task: Add `keyboard` library to dependencies. [checkpoint: d18c394]
- [x] Task: Strip `engine/interaction.py`. [checkpoint: 38024ab]
    - [x] Remove `queue.Queue`.
    - [x] Remove `_worker_loop` and `WorkerThread`.
    - [x] Refactor `InputMonitor` to use `keyboard` hooks instead of `pynput.Listener`.
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Architectural Integration
- [x] Task: Simplify `main.py` (`AppCoordinator`). [checkpoint: 38024ab]
- [x] Task: Implement dynamic hotkey switching. [checkpoint: 4390596]
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Validation & Tests
- [ ] Task: Update unit tests.
    - Refactor `tests/test_interaction.py` to account for the new library.
- [ ] Task: Manual Leakage Verification.
    - Verify zero leakage in Notepad.
- [ ] Task: Run full "Definition of Done Gate".
    - `uv run ruff check .`
    - `uv run ruff format --check .`
    - `uv run mypy .`
    - `uv run pytest -q`
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)
