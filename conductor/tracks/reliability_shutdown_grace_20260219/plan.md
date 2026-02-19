# Implementation Plan: Reliability & Shutdown Grace

## Phase 1: Shutdown Cleanliness (Fixing the Crash)
- [x] **Task:** Refactor `main_gui` to use a non-daemon UI thread and clean join. [02a5e18]
- [x] **Task:** Update `TrayApp.stop` to ensure the `pystray` icon is closed properly. [02a5e18]
- [x] **Task:** Add `repro_shutdown.py` to verify no fatal errors on Ctrl+C. [02a5e18]

## Phase 2: Hotkey Reliability (Fixing the Stale Hook)
- [x] **Task:** Research stability of `keyboard` vs `pynput`. (Decision: Keep `keyboard` + Heartbeat)
- [x] **Task:** Implement `InputMonitor.restart()` and a 60-minute "Refresh" timer in `AppCoordinator`. [02a5e18]
- [ ] **Task:** Verify hotkey suppression still works as intended.

## Phase 3: Validation
- [ ] **Task:** Run DoD Gate (ruff, mypy, pytest).
- [ ] **Task:** Manual "Multi-Hour" soak test (simulated).
