# Implementation Plan: Reliability & Shutdown Grace v2

## Phase 1: Native Hook & Shutdown
- [ ] **Task:** Implement `Win32InputMonitor` in `engine/interaction.py` using `ctypes` and `WH_KEYBOARD_LL`.
- [ ] **Task:** Integrate the "Stuck Modifier" release logic (`_release_stuck_modifiers`).
- [ ] **Task:** Refactor `main_gui` and `TrayApp` for non-daemon thread join.
- [ ] **Task:** Add `repro_shutdown_v2.py` to verify clean exit.

## Phase 2: Session Monitoring (Fixing Lock/Unlock)
- [ ] **Task:** Implement `SessionMonitor` in `engine/platform_win/session.py`.
- [ ] **Task:** Connect `SessionMonitor` to `AppCoordinator` to trigger hook re-initialization on Unlock.
- [ ] **Task:** Add `repro_lock_unlock.py` to simulate/verify desktop switch recovery.

## Phase 3: Validation
- [ ] **Task:** Run DoD Gate (ruff, mypy, pytest).
- [ ] **Task:** Manual verification of Toggle/Hold mode hotkey suppression.
