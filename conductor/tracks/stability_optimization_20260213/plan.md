# Implementation Plan: Stability & Optimization

Remove heavy dependencies and optimize UI loading.

## Phase 1: Lightweight Anchor (I6)
Goal: Replace `pywin32` with `ctypes`.

- [ ] Task: Create `engine/win32_utils.py` (or similar) or just inline `ctypes` definitions in `engine/anchor.py`.
- [ ] Task: Implement `GetForegroundWindow`, `GetWindowThreadProcessId`, `WindowFromPoint`, `GetAncestor` using `ctypes`.
- [ ] Task: Refactor `Anchor.capture_current` and `is_match` to use the new ctypes functions.
- [ ] Task: Remove `win32gui` and `win32process` imports.
- [ ] Task: Conductor - User Manual Verification 'Anchor Refactor'

## Phase 2: Lazy Indicator (I5)
Goal: Make the floating indicator strictly optional.

- [ ] Task: Update `engine/config.py` to default `floating_indicator.enabled` to `False`.
- [ ] Task: Refactor `engine/ui.py` to import `IndicatorWindow` only inside `__init__` (or a setup method) and only if enabled.
- [ ] Task: Ensure `TrayApp` handles a `None` indicator gracefully (noop calls).
- [ ] Task: Conductor - User Manual Verification 'Lazy Indicator'

## Phase 3: Verification
Goal: Ensure no regressions.

- [ ] Task: Run full test suite.
- [ ] Task: Pass DOD Gate.
