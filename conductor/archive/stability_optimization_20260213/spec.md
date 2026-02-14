# Track Specification: Stability & Optimization

## Overview
Improve application stability and reduce footprint by removing heavy dependencies (`pywin32`) and optimizing UI resource usage. This track directly addresses consultant recommendations I5 (UI) and I6 (Anchor Bloat).

## 1. Functional Scope

### 1.1 Lightweight Anchor Capture (I6)
- **Goal:** Replace `pywin32` with `ctypes` in `engine/anchor.py`.
- **Logic:** Implement `GetForegroundWindow`, `GetWindowThreadProcessId`, `WindowFromPoint`, and `GetAncestor` using `ctypes.windll.user32`.
- **Benefit:** Removes a massive dependency that can cause DLL conflicts and hangs.

### 1.2 Lazy UI Indicator (I5)
- **Goal:** Prevent unnecessary resource usage and potential crashes on startup.
- **Logic:**
    - Default `floating_indicator.enabled` to `false` in config.
    - Only import/create `IndicatorWindow` if enabled.
    - Treat the indicator as an optional enhancement, not a core requirement.

## 2. Technical Goals
- **Dependency Reduction:** Eliminate `win32gui` and `win32process` imports.
- **Startup Speed:** Reduce import time by lazy-loading heavy UI modules.
- **Crash Resistance:** Isolate the brittle GDI+/Skia overlay code.

## 3. Acceptance Criteria
- [ ] `engine/anchor.py` has zero imports from `pywin32` (win32gui, etc).
- [ ] `engine/ui.py` does not import `IndicatorWindow` at module level.
- [ ] Application functions correctly even if the indicator crashes or is disabled.
- [ ] Passes DOD Gate.
