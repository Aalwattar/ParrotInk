# Implementation Plan: Interactive Hotkey Configuration & Generalized Config Sync

Enable users to dynamically change the global hotkey via the tray menu and implement a robust, generalized synchronization mechanism between the UI settings and the application configuration.

## Phase 1: Generalized Configuration Synchronization
Goal: Create a central service to handle configuration updates and state propagation.

- [ ] Task: Create `engine/config_sync.py`.
- [ ] Task: Implement `ConfigSynchronizer` class.
    - [ ] Sub-task: Method to update `config.toml` using `tomli-w`.
    - [ ] Sub-task: Method to notify registered observers of setting changes (Observer Pattern).
- [ ] Task: Integrate `ConfigSynchronizer` into `AppCoordinator`.
- [ ] Task: Conductor - User Manual Verification 'Generalized Configuration Synchronization' (Protocol in workflow.md)

## Phase 2: Interactive Hotkey Recording Logic
Goal: Implement the logic to capture raw keyboard input and validate it.

- [ ] Task: Create `engine/platform_win/hotkey_recorder.py`.
- [ ] Task: Implement `HotkeyRecorder` using `pynput` to listen for a single "combination" event.
- [ ] Task: Implement validation logic to reject "Major No-Nos" (Win+L, Alt+F4, etc.).
- [ ] Task: Create a basic Win32 modal prompt logic using `MessageBoxW`.
- [ ] Task: Conductor - User Manual Verification 'Interactive Hotkey Recording Logic' (Protocol in workflow.md)

## Phase 3: Tray UI Integration & Reactive Sync
Goal: Connect the recording logic to the tray menu and ensure live updates.

- [ ] Task: Update `engine/ui.py` (pystray menu) to add the "Change Hotkey" option.
- [ ] Task: Implement the "Change Hotkey" action handler:
    - [ ] Sub-task: Show prompt.
    - [ ] Sub-task: Start recorder.
    - [ ] Sub-task: On success, use `ConfigSynchronizer` to persist and apply.
- [ ] Task: Update `InteractionMonitor` to support hotkey rotation without restart.
- [ ] Task: Conductor - User Manual Verification 'Tray UI Integration & Reactive Sync' (Protocol in workflow.md)

## Phase 4: Verification & Hardening
Goal: Ensure zero regressions and robust error handling.

- [ ] Task: Run full test suite.
- [ ] Task: Manual verification of hotkey changes across different apps (Notepad, Browser).
- [ ] Task: Pass DOD Gate (Ruff, Mypy, Pytest).
- [ ] Task: Conductor - User Manual Verification 'Verification & Hardening' (Protocol in workflow.md)
