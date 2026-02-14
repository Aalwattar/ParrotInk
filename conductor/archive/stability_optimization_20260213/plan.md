# Implementation Plan: Stability & Optimization

Remove heavy dependencies and optimize UI loading.

## Phase 1: Lightweight Anchor (I6)
Goal: Replace `pywin32` with `ctypes`.

- [x] Task: Create `engine/win32_utils.py` (or similar) or just inline `ctypes` definitions in `engine/anchor.py`.
- [x] Task: Implement `GetForegroundWindow`, `GetWindowThreadProcessId`, `WindowFromPoint`, `GetAncestor` using `ctypes`.
- [x] Task: Refactor `Anchor.capture_current` and `is_match` to use the new ctypes functions.
- [x] Task: Remove `win32gui` and `win32process` imports.
- [x] Task: Conductor - User Manual Verification 'Anchor Refactor'

## Phase 2: Lazy Indicator (I5)
Goal: Make the floating indicator strictly optional.

- [x] Task: Update `engine/config.py` to default `floating_indicator.enabled` to `False`.
- [x] Task: Refactor `engine/ui.py` to import `IndicatorWindow` only inside `__init__` (or a setup method) and only if enabled.
- [x] Task: Ensure `TrayApp` handles a `None` indicator gracefully (noop calls).
- [x] Task: Conductor - User Manual Verification 'Lazy Indicator'

## Phase 3: Verification
Goal: Ensure no regressions.

- [x] Task: Run full test suite.
- [x] Task: Pass DOD Gate.
