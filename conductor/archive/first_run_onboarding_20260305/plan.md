# Implementation Plan: First-Run Onboarding Popup

## Phase 1: Configuration & CLI Setup [checkpoint: 56b5cdd]
- [x] Task: Update the `pyproject.toml` and `engine/config.py` definitions to include `ui.show_onboarding_popup` (default: true). a595e73
- [x] Task: Modify `main.py` CLI parsing to properly handle the `--background` argument, ensuring it takes precedence over the config value. a595e73
- [x] Task: Write tests (`tests/test_config_onboarding.py`) to verify the default state, loaded state, and CLI precedence logic. a595e73
- [x] Task: Conductor - User Manual Verification 'Phase 1: Configuration & CLI Setup' (Protocol in workflow.md)

## Phase 2: Popup UI Implementation [checkpoint: fd4b932]
- [x] Task: Create a new module `engine/onboarding_ui.py` (or integrate into `engine/ui.py`) to build the popup using `ttkbootstrap`. 98b7fb0
- [x] Task: Design the UI layout: Title, explanatory text, tray icon examples, and the "Don't show this again" checkbox. 98b7fb0
- [x] Task: Implement the "OK" button logic to capture the state of the checkbox. 98b7fb0
- [x] Task: Conductor - User Manual Verification 'Phase 2: Popup UI Implementation' (Protocol in workflow.md)

## Phase 3: Integration & State Management [checkpoint: 632cfee]
- [x] Task: Integrate the popup into the application startup sequence in `main.py` or the `AppCoordinator`. 15c0d75
- [x] Task: Implement the logic to save the new `ui.show_onboarding_popup` state back to `config.toml` (using the existing `tomlkit` logic) if the user checked the box. 15c0d75
- [x] Task: Write integration tests (`tests/test_onboarding_integration.py`) to simulate startup scenarios, ensuring the popup is shown/hidden correctly based on config and CLI args, and that saving config works. 15c0d75
- [x] Task: Conductor - User Manual Verification 'Phase 3: Integration & State Management' (Protocol in workflow.md)

## Phase: Review Fixes
- [x] Task: Apply review suggestions 68d2599
