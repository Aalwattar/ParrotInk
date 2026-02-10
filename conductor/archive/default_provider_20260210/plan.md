# Implementation Plan: Default Provider & UI Validation

## Phase 1: Config Refactoring & Fallback [checkpoint: b068399]
Rename the core configuration field and ensure robust defaults.

- [x] Task: Rename `active_provider` to `default_provider` in `engine/config.py` [b068399]
    - [x] Update `Config` class field name and default value.
    - [x] Update `Config.from_file` to handle potential migration or missing keys gracefully.
- [x] Task: Write tests for config renaming and fallbacks [b068399]
    - [x] **Red:** Write tests in `tests/test_config.py` that check for `default_provider` presence and fallback to "openai" if missing.
    - [x] **Green:** Ensure all config tests pass.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Config Refactoring & Fallback' (Protocol in workflow.md)

## Phase 2: Availability Logic [checkpoint: 58c417f]
Implement the logic to check if a provider can be used based on keys and test mode.

- [x] Task: Implement `is_provider_available` logic [58c417f]
    - [x] Add a helper method in `AppCoordinator` or a separate utility to check key presence vs `test.enabled`.
- [x] Task: Write unit tests for availability logic [58c417f]
    - [x] **Red:** Write tests in `tests/test_availability.py` (or similar) to verify availability states for both providers under various config scenarios.
    - [x] **Green:** Ensure availability tests pass.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Availability Logic' (Protocol in workflow.md)

## Phase 3: UI Integration (Graying Out) [checkpoint: 58c417f]
Update the system tray to reflect availability.

- [x] Task: Update `TrayApp` to support disabling menu items [58c417f]
    - [x] Modify `engine/ui.py` to allow passing a 'disabled' or 'enabled' state to the provider radio items.
- [x] Task: Connect Coordinator availability to UI [58c417f]
    - [x] Update `main.py` to pass the availability map to the `TrayApp` during initialization.
- [x] Task: Write tests for UI state updates [58c417f]
    - [x] **Red:** Write tests in `tests/test_ui.py` to verify that menu items can be disabled.
    - [x] **Green:** Ensure UI tests pass.
- [x] Task: Conductor - User Manual Verification 'Phase 3: UI Integration (Graying Out)' (Protocol in workflow.md)

## Phase 4: Final Verification [checkpoint: 58c417f]
Ensure the app behaves correctly when providers are missing.

- [x] Task: Perform end-to-end smoke test [58c417f]
    - [x] Run with empty keys and `test.enabled = false` -> Verify grayed out menu.
    - [x] Run with empty keys and `test.enabled = true` -> Verify all menu items enabled.
- [x] Task: Conductor - User Manual Verification 'Phase 4: Final Verification' (Protocol in workflow.md)
