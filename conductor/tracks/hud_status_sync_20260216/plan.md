# Implementation Plan: HUD & Status Synchronization

## Phase 1: Investigative Trace & State Audit [checkpoint: 6750e96]
- [x] Audit `engine/app_coordinator.py` (or `main.py`) and `engine/connection.py` for all state transition triggers. 6750e96
- [x] Verify that every `set_state` call correctly propagates to both `TrayApp` and `IndicatorWindow`. 6750e96
- [x] Identify missing "Refresh" signals in the `UIBridge`. 6750e96

## Phase 2: Centralized Status Propagation [checkpoint: 6750e96]
- [x] Refactor `UIBridge` to include explicit `UPDATE_PROVIDER` and `UPDATE_SETTINGS` events. 6750e96
- [x] Update `IndicatorWindow` to handle these events and redraw its capsule immediately. 6750e96
- [x] Ensure `TrayApp.set_state` and `IndicatorWindow.update_status` are fully idempotent and consistent. 6750e96

## Phase 3: Cleanup & Robustness [checkpoint: 6750e96]
- [x] Implement a "Force Reset" for the HUD when a new session starts to clear stale text. 6750e96
- [x] Add tests for concurrent state updates to ensure the UI remains consistent. 6750e96
- **Verification**: Manually verified provider switching and tooltip sync. Automated tests passed. 6750e96
