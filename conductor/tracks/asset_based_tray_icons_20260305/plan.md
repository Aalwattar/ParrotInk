# Implementation Plan: Asset-Based Tray Icons

## Phase 1: Investigation & Test Harness
- [ ] Task: Create a new test file `tests/test_ui_icon_loading.py` to verify that the UI can load and fall back when icons are missing.
- [ ] Task: Review the existing `UI` class in `engine/ui.py` to identify the current icon generation and state mapping logic.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Investigation & Test Harness' (Protocol in workflow.md)

## Phase 2: Implementation (The "Robust Icon Logic")
- [ ] Task: Modify the `UI` class to include an icon caching mechanism.
- [ ] Task: Implement the `_get_icon_asset` logic:
    - Attempt to load the corresponding `.ico` file based on the `AppState`.
    - If successful, return the icon asset.
    - If the file is missing or cannot be loaded, fall back to the dynamic color generation logic.
- [ ] Task: Update the `_create_icon` and `on_state_changed` methods to utilize the new asset-based loading.
- [ ] Task: Ensure the current state color definitions (`COLOR_IDLE`, `COLOR_LISTENING`, etc.) are preserved for the fallback case.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Implementation' (Protocol in workflow.md)

## Phase 3: Final Verification
- [ ] Task: Run all UI tests to ensure no regressions in tray menu functionality or HUD synchronization.
- [ ] Task: Verify that the application correctly handles the absence of assets by showing the original colored squares.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Final Verification' (Protocol in workflow.md)
---
**Note:** Once you provide the `.ico` files in `assets/icons/`, the application will automatically pick them up based on this logic.
