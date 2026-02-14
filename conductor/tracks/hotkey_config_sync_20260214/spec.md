# Specification: Interactive Hotkey Configuration & Generalized Config Sync

Enable users to dynamically change the global hotkey via the tray menu and implement a robust, generalized synchronization mechanism between the UI settings and the application configuration.

## 1. Overview
This track addresses two key needs:
1.  **Interactive Hotkey Recording:** A user-friendly way to "record" a new hotkey from the tray.
2.  **Generalized Configuration Sync:** A central service to ensure that *any* setting change made in the UI is immediately persisted to `config.toml` and applied to the running application state.

## 2. Functional Requirements

### 2.1. Interactive Hotkey Recording
- **Tray Entry:** Add "Change Hotkey" to the tray menu.
- **Recording UI:** Display a modal dialog ("Press your new hotkey...") to capture input.
- **Validation:** 
    - Reject system-reserved shortcuts (Alt+F4, Win+L, etc.).
    - Ensure the combination is valid for `pynput`/`InteractionMonitor`.
- **Success:** Notify the user when the hotkey is updated.

### 2.2. Generalized Configuration Sync Service
- **Unified Sync Logic:** Implement a central function or class (e.g., `ConfigSynchronizer`) responsible for:
    - Writing specific setting updates to `config.toml`.
    - Notifying relevant application components (AppCoordinator, InteractionMonitor, etc.) that a specific configuration value has changed.
- **Reactive Updates:** When a user changes *any* setting via the tray menu (e.g., changing providers, toggling HUD, or updating hotkeys), this service should be used to ensure the change is permanent and effective immediately.
- **Library Choice:** Ensure the implementation uses existing configuration libraries (`pydantic`, `tomli-w`) consistently.

### 2.3. Code Organization
- **Separation of Concerns:** Keep the "Hotkey Recording" logic (keyboard capture) separate from the "Config Sync" logic (persistence and state propagation).
- **New Modules:** 
    - `engine/ui_bridge.py` (or similar): Handle the bridge between UI actions and engine commands.
    - `engine/config_sync.py`: The centralized service for config updates.

## 3. Technical Constraints
- Use existing `Config` (Pydantic) models for validation during sync.
- Use `tomli-w` for clean TOML writes.
- Avoid redundant disk I/O; sync should be efficient.
- Ensure thread safety when updating the configuration and notifying components.

## 4. Acceptance Criteria
- [ ] User can record a new hotkey via the tray menu.
- [ ] Invalid hotkeys are rejected with clear feedback.
- [ ] **Synchronization:** Any setting changed via the UI is immediately reflected in `config.toml`.
- [ ] **Live Update:** The application state (e.g., the hotkey listener) updates in real-time without a restart.
- [ ] The sync logic is reusable for future settings added to the UI.

## 5. Out of Scope
- Redesigning the entire `config.py` structure.
- Complex multi-tab settings window (maintaining tray-based interaction).
