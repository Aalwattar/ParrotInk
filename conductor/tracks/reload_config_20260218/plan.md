# Implementation Plan - Reload Configuration

This plan covers the implementation of a manual configuration reload feature, allowing users to sync edits to `config.toml` without restarting the application.

## Phase 0: Architectural Alignment & Simplicity Check
Before writing any code, we will align on the simplest, most robust architecture for each component.

- [x] Task: Architectural Discussion: `engine/config.py`
    - [x] Discuss the `reload()` method implementation.
    - [x] Ensure no shortcuts are taken with Pydantic validation.
    - [x] Evaluate if `Config` should remain a singleton-like instance or if a fresh instance should be swapped.
- [x] Task: Architectural Discussion: `engine/ui.py` & `gui_main.py`
    - [x] Discuss the menu placement and callback structure.
    - [x] Evaluate future-proofing: How will this "Reload" logic translate if we move to a full GUI in the future?
- [x] Task: Simplicity Review
    - [x] Explore if there is an even simpler way to trigger a reload (e.g., does it belong as a "Refresh" button inside an editor, or is the Tray Menu item the absolute minimum debt?).

## Phase 1: Core Logic (Engine)
Implementation of the reload mechanism within the configuration and coordination layers.

- [x] Task: Implement `Config.reload()` logic
    - [x] Write unit tests in `tests/test_config_lifecycle.py` to verify `reload()` correctly updates fields from disk and notifies observers.
    - [x] Implement `reload()` in `engine/config.py` using `tomllib` and existing Pydantic validation.
    - [x] Verify tests pass (Green phase).
- [x] Task: Update `AppCoordinator` to handle manual reloads
    - [x] Write tests to ensure `AppCoordinator` reacts to a full configuration refresh (e.g., hotkey update).
    - [x] Refine `AppCoordinator._on_config_changed` if necessary to ensure all live components sync correctly.
    - [x] Verify tests pass.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Core Logic' (Protocol in workflow.md)

## Phase 2: UI Integration (Tray & Bridge)
Adding the user interface elements and connecting them to the engine logic.

- [x] Task: Add "Reload Configuration" to Tray Menu
    - [x] Update `TrayApp` in `engine/ui.py` to include the new menu item under Settings.
    - [x] Add `on_reload_config` callback to `TrayApp` constructor and internal logic.
- [x] Task: Wire the reload action in `gui_main`
    - [x] Implement the `on_reload_config` callback in `engine/gui_main.py`.
    - [x] Connect the UI trigger to the `coordinator.config.reload()` call.
- [x] Task: Conductor - User Manual Verification 'Phase 2: UI Integration' (Protocol in workflow.md)

## Phase 3: User Feedback & Error Handling
Polishing the experience with success and failure notifications.

- [x] Task: Implement Success Feedback (Tooltip/Toast)
    - [x] Update `UIBridge` and `TrayApp` to support a temporary tooltip status change or success toast.
    - [x] Trigger the feedback upon successful reload.
- [x] Task: Implement Failure Feedback (MessageBox)
    - [x] Add logic in `gui_main` to catch `ConfigError` during reload.
    - [x] Use `ctypes.windll.user32.MessageBoxW` to display validation errors to the user.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Feedback' (Protocol in workflow.md)

## Phase: Review Fixes
- [x] Task: Apply review suggestions 4b38240
