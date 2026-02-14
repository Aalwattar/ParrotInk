# Implementation Plan: Run at Startup Feature

## Phase 1: Foundation & Registry Logic
Goal: Implement the core Windows Registry manipulation logic in a dedicated module.

- [x] Task: Create `engine/platform_win/startup.py` with registry management functions. [7302392]
    - [x] Task: Implement `set_run_at_startup(enabled: bool)` using `winreg` to create/delete the "Voice2Text" **value**.
    - [x] Task: Implement `is_run_at_startup_synced() -> bool` to check if registry matches current exe path.
    - [x] Task: Ensure the executable path is correctly resolved for both script and EXE modes.
- [x] Task: Update `engine/config.py` to include the new setting. [0b6c0f7]
    - [x] Task: Add `run_at_startup: bool = False` to `InteractionConfig`.
- [x] Task: Write unit tests for the startup logic. [7302392]
    - [x] Task: Create `tests/test_startup_win.py` to verify registry value manipulation (using mocks).
- [ ] Task: Conductor - User Manual Verification 'Foundation & Registry Logic' (Protocol in workflow.md)

## Phase 2: Integration & UI
Goal: Connect the registry logic to the configuration system and the tray UI.

- [ ] Task: Implement "Startup Sync" in `main.py`.
    - [ ] Task: On app initialization, if `config.interaction.run_at_startup` is true, call `set_run_at_startup(True)`.
- [ ] Task: Update `engine/ui.py` to add the tray menu toggle.
    - [ ] Task: Add "Run at Startup" to the Settings menu.
    - [ ] Task: Implement click handler: `config.update_and_save(...)` -> then call `set_run_at_startup(...)` immediately.
- [ ] Task: Verify end-to-end flow.
    - [ ] Task: Toggle the setting via UI and check `config.toml` and Registry.
    - [ ] Task: Pass DOD Gate (Ruff, Mypy, Pytest).
- [ ] Task: Conductor - User Manual Verification 'Integration & UI' (Protocol in workflow.md)
