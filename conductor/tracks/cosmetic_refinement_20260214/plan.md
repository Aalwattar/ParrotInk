# Implementation Plan: Cosmetic & UI Refinements

## Phase 1: Visual Foundation & Icons [checkpoint: fc153a6]
Goal: Modernize the tray icon and HUD typography.

- [x] Task: Create `engine/ui_utils.py` for shared UI helpers. [bffa869]
    - [x] Task: Implement `get_app_version() -> str` by parsing `pyproject.toml`. [bffa869]
- [x] Task: Refactor `TrayApp` icon generation in `engine/ui.py`. [b64c8bb]
    - [x] Task: Replace the ellipse design with a rounded-corner square ("Modern Square"). [b64c8bb]
    - [x] Task: Update color palette for Idle, Listening, and Error states to be more "Fluent/Modern". [b64c8bb]
- [x] Task: Update HUD Typography in `engine/hud_styles.py`. [e35f1b3]
    - [x] Task: Change default font to "Segoe UI". [e35f1b3]
    - [x] Task: Adjust font size to the lower end of the high-readability range (e.g., 14pt-16pt). [e35f1b3]
- [ ] Task: Conductor - User Manual Verification 'Visual Foundation & Icons' (Protocol in workflow.md)

## Phase 2: Tray Menu & Feature Exposure
Goal: Add the version header and "Hold to Talk" toggle to the Tray.

- [x] Task: Update `TrayApp._create_icon` in `engine/ui.py`. [4e1f231]
    - [x] Task: Add the disabled version header at the top of the menu. [4e1f231]
    - [x] Task: Add the "Hold to Talk" toggle in the Settings sub-menu. [4e1f231]
- [x] Task: Implement "Hold to Talk" logic in `engine/gui_main.py`. [4e1f231]
    - [x] Task: Connect the tray callback to `config.update_and_save()`. [4e1f231]
- [x] Task: Verify end-to-end flow. [4e1f231]
    - [x] Task: Check that toggling "Hold to Talk" in Tray updates `config.toml`. [4e1f231]
    - [x] Task: Verify version display correctly reflects `pyproject.toml`. [4e1f231]
    - [x] Task: Pass DOD Gate (Ruff, Mypy, Pytest). [4e1f231]
- [ ] Task: Conductor - User Manual Verification 'Tray Menu & Feature Exposure' (Protocol in workflow.md)
