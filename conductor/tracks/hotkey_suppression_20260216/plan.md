# Implementation Plan: Hotkey Input Suppression (Anti-Leak)

This track addresses the issue where non-modifier keys in the hotkey combination (like 'Space') are leaked to the active window.

## Phase 1: Research & Infrastructure
- [x] Task: Research `pynput` and `pywin32` suppression capabilities. [checkpoint: e9b56b8]
    - [x] Determine if the current `InputMonitor` (based on `pynput`) can selectively suppress events by returning `False` from the listener. (Found: `win32_event_filter` allows this).
    - [x] Verify if a low-level Win32 `WH_KEYBOARD_LL` hook is required for more reliable suppression. (Found: `pynput` already uses this, `win32_event_filter` exposes it).
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Implementation & TDD
- [x] Task: Create a reproduction test case for key leakage. [checkpoint: 8daf51c]
- [x] Task: Implement selective suppression in `engine/interaction.py`. [checkpoint: 8daf51c]
- [x] Task: Verify fix with reproduction test. [checkpoint: 8daf51c]
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Final Validation
- [~] Task: Run full "Definition of Done Gate".
    - [ ] `uv run ruff check .`
    - [ ] `uv run ruff format --check .`
    - [ ] `uv run mypy .`
    - [ ] `uv run pytest -q`
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)
