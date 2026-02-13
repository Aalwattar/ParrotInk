# Implementation Plan: Consultant Security & Stability Improvements

Apply security and stability improvements to keyboard handling, logging, credentials, and evaluation signaling.

## Phase 1: Logging & Credentials (Quick Wins)
Goal: Address low-complexity security and resource management issues.

- [ ] Task: Implement `shutdown_logging()` in `engine/logging.py`.
- [ ] Task: Integrate `shutdown_logging()` into `AppCoordinator.shutdown` in `main.py`.
- [ ] Task: Update `engine/credential_ui.py` to use `getpass.getpass()`.
- [ ] Task: Verify fix with a manual test of the credential prompt.
- [ ] Task: Conductor - User Manual Verification 'Logging & Credentials'

## Phase 2: Eval Mode Signaling
Goal: Fix termination reliability for the evaluation harness.

- [ ] Task: Modify `engine/eval_main.py` to set `self.finished_event` in `on_final`.
- [ ] Task: Refactor `run()` in `eval_main.py` to remove redundant grace period waits if already finished.
- [ ] Task: Run a sample evaluation to verify immediate termination.
- [ ] Task: Conductor - User Manual Verification 'Eval Mode Fix'

## Phase 3: Unified Input Monitoring
Goal: Consolidate keyboard hooks into a single managed instance.

- [ ] Task: Design a unified `InputMonitor` class that handles both Hotkeys and Any-Key-Press cancellation.
- [ ] Task: Refactor `engine/gui_main.py` to use the new `InputMonitor`.
- [ ] Task: Refactor `engine/interaction.py` to use the new `InputMonitor` (removing its internal listener).
- [ ] Task: Verify hotkey toggle and "stop on any key" functionality still work correctly.
- [ ] Task: Conductor - User Manual Verification 'Unified Input Monitor'

## Phase 4: Verification & DOD Gate
Goal: Ensure zero regressions and compliance with project standards.

- [ ] Task: Run full test suite: `uv run pytest`.
- [ ] Task: Pass DOD Gate:
    - [ ] `uv run ruff check .`
    - [ ] `uv run ruff format .`
    - [ ] `uv run mypy .`
- [ ] Task: Conductor - User Manual Verification 'Consultant Improvements Finalization'
