# Implementation Plan: Reliability & Shutdown Grace v2

## Phase 1: Native Hook & Shutdown
- [x] **Task:** Implement `Win32InputMonitor` in `engine/interaction.py` using `ctypes` and `WH_KEYBOARD_LL`. [1f2028f]
- [x] **Task:** Integrate the "Stuck Modifier" release logic (`_release_stuck_modifiers`). [1f2028f]
- [x] **Task:** Refactor `main_gui` and `TrayApp` for non-daemon thread join. [1f2028f]
- [x] **Task:** Add `repro_shutdown_v2.py` to verify clean exit. [1f2028f]

## Phase 2: Session Monitoring (Fixing Lock/Unlock)
- [x] **Task:** Implement `SessionMonitor` in `engine/platform_win/session.py`. [1f2028f]
- [x] **Task:** Connect `SessionMonitor` to `AppCoordinator` to trigger hook re-initialization on Unlock. [1f2028f]
- [x] **Task:** Add `repro_lock_unlock.py` to simulate/verify desktop switch recovery. [72274e3]

## Phase 3: Validation
- [x] **Task:** Run DoD Gate (ruff, mypy, pytest). [f316ecd]
- [x] **Task:** Manual verification of Toggle/Hold mode hotkey suppression. [f316ecd]
