# Implementation Plan: Hotkey Input Suppression (Anti-Leak)

This track addresses the issue where non-modifier keys in the hotkey combination (like 'Space') are leaked to the active window.

## Phase 1: Research & Infrastructure
- [ ] Task: Research `pynput` and `pywin32` suppression capabilities.
    - [ ] Determine if the current `InputMonitor` (based on `pynput`) can selectively suppress events by returning `False` from the listener.
    - [ ] Verify if a low-level Win32 `WH_KEYBOARD_LL` hook is required for more reliable suppression.
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Implementation & TDD
- [ ] Task: Create a reproduction test case for key leakage.
    - [ ] **Red Phase**: Write a test in `tests/test_suppression.py` that simulates a `Ctrl+Space` press and asserts that the `Space` event is marked as suppressed/handled.
    - [ ] Confirm the test fails with the current implementation.
- [ ] Task: Implement selective suppression in `engine/interaction.py`.
    - [ ] **Green Phase**: Update the `InputMonitor` to return `False` (or use the equivalent Win32 suppression) specifically for keys matching the `target_hotkey`.
    - [ ] Ensure the `AppCoordinator` still receives the event to trigger dictation.
- [ ] Task: Verify fix with reproduction test.
    - [ ] Rerun `tests/test_suppression.py` and confirm it passes.
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Final Validation
- [ ] Task: Run full "Definition of Done Gate".
    - [ ] `uv run ruff check .`
    - [ ] `uv run ruff format --check .`
    - [ ] `uv run mypy .`
    - [ ] `uv run pytest -q`
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)
