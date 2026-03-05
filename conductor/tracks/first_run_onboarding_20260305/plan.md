# Implementation Plan: First-Run Onboarding Popup

## Phase 1: Configuration & CLI Setup
- [ ] Task: Update the `pyproject.toml` and `engine/config.py` definitions to include `ui.show_onboarding_popup` (default: true).
- [ ] Task: Modify `main.py` CLI parsing to properly handle the `--background` argument, ensuring it takes precedence over the config value.
- [ ] Task: Write tests (`tests/test_config_onboarding.py`) to verify the default state, loaded state, and CLI precedence logic.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Configuration & CLI Setup' (Protocol in workflow.md)

## Phase 2: Popup UI Implementation
- [ ] Task: Create a new module `engine/onboarding_ui.py` (or integrate into `engine/ui.py`) to build the popup using `ttkbootstrap`.
- [ ] Task: Design the UI layout: Title, explanatory text, tray icon examples, and the "Don't show this again" checkbox.
- [ ] Task: Implement the "OK" button logic to capture the state of the checkbox.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Popup UI Implementation' (Protocol in workflow.md)

## Phase 3: Integration & State Management
- [ ] Task: Integrate the popup into the application startup sequence in `main.py` or the `AppCoordinator`.
- [ ] Task: Implement the logic to save the new `ui.show_onboarding_popup` state back to `config.toml` (using the existing `tomlkit` logic) if the user checked the box.
- [ ] Task: Write integration tests (`tests/test_onboarding_integration.py`) to simulate startup scenarios, ensuring the popup is shown/hidden correctly based on config and CLI args, and that saving config works.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Integration & State Management' (Protocol in workflow.md)
