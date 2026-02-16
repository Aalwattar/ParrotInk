# Implementation Plan: HUD & Status Synchronization

## Phase 1: Investigative Trace & State Audit
- [~] Audit `engine/app_coordinator.py` (or `main.py`) and `engine/connection.py` for all state transition triggers.
- [ ] Verify that every `set_state` call correctly propagates to both `TrayApp` and `IndicatorWindow`.
- [ ] Identify missing "Refresh" signals in the `UIBridge`.

## Phase 2: Centralized Status Propagation
- [ ] Refactor `UIBridge` to include explicit `UPDATE_PROVIDER` and `UPDATE_SETTINGS` events.
- [ ] Update `IndicatorWindow` to handle these events and redraw its capsule immediately.
- [ ] Ensure `TrayApp.set_state` and `IndicatorWindow.update_status` are fully idempotent and consistent.

## Phase 3: Cleanup & Robustness
- [ ] Implement a "Force Reset" for the HUD when a new session starts to clear stale text.
- [ ] Add tests for concurrent state updates to ensure the UI remains consistent.
- **Verification**: Manually toggle all settings; verify HUD and Tray sync in real-time.
