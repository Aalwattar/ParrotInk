# Implementation Plan: Reliability & Shutdown Grace

## Phase 1: Shutdown Cleanliness (Fixing the Crash)
- [ ] **Task:** Refactor `main_gui` to use a non-daemon UI thread and clean join.
- [ ] **Task:** Update `TrayApp.stop` to ensure the `pystray` icon is closed properly.
- [ ] **Task:** Add `repro_shutdown.py` to verify no fatal errors on Ctrl+C.

## Phase 2: Hotkey Reliability (Fixing the Stale Hook)
- [ ] **Task:** Research/Test if `pynput` is more stable for long-term (multi-hour) Windows hooks.
- [ ] **Task:** Implement `InputMonitor.restart()` and a 60-minute "Refresh" timer in `AppCoordinator`.
- [ ] **Task:** Verify hotkey suppression still works as intended.

## Phase 3: Validation
- [ ] **Task:** Run DoD Gate (ruff, mypy, pytest).
- [ ] **Task:** Manual "Multi-Hour" soak test (simulated).
