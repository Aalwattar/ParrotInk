# Implementation Plan: Default Provider & UI Validation

## Phase 1: Config Refactoring & Fallback
Rename the core configuration field and ensure robust defaults.

- [ ] Task: Rename `active_provider` to `default_provider` in `engine/config.py`
    - [ ] Update `Config` class field name and default value.
    - [ ] Update `Config.from_file` to handle potential migration or missing keys gracefully.
- [ ] Task: Write tests for config renaming and fallbacks
    - [ ] **Red:** Write tests in `tests/test_config.py` that check for `default_provider` presence and fallback to "openai" if missing.
    - [ ] **Green:** Ensure all config tests pass.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Config Refactoring & Fallback' (Protocol in workflow.md)

## Phase 2: Availability Logic
Implement the logic to check if a provider can be used based on keys and test mode.

- [ ] Task: Implement `is_provider_available` logic
    - [ ] Add a helper method in `AppCoordinator` or a separate utility to check key presence vs `test.enabled`.
- [ ] Task: Write unit tests for availability logic
    - [ ] **Red:** Write tests in `tests/test_coordinator.py` (or similar) to verify availability states for both providers under various config scenarios.
    - [ ] **Green:** Ensure availability tests pass.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Availability Logic' (Protocol in workflow.md)

## Phase 3: UI Integration (Graying Out)
Update the system tray to reflect availability.

- [ ] Task: Update `TrayApp` to support disabling menu items
    - [ ] Modify `engine/ui.py` to allow passing a 'disabled' or 'enabled' state to the provider radio items.
- [ ] Task: Connect Coordinator availability to UI
    - [ ] Update `main.py` to pass the availability map to the `TrayApp` during initialization.
- [ ] Task: Write tests for UI state updates
    - [ ] **Red:** Write tests in `tests/test_ui.py` to verify that menu items can be disabled.
    - [ ] **Green:** Ensure UI tests pass.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: UI Integration (Graying Out)' (Protocol in workflow.md)

## Phase 4: Final Verification
Ensure the app behaves correctly when providers are missing.

- [ ] Task: Perform end-to-end smoke test
    - [ ] Run with empty keys and `test.enabled = false` -> Verify grayed out menu.
    - [ ] Run with empty keys and `test.enabled = true` -> Verify all menu items enabled.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Final Verification' (Protocol in workflow.md)
