# Specification - Reload Configuration Feature

## Overview
This feature allows users to manually reload the application's configuration from the `config.toml` file on disk without restarting the application. It provides a way to sync manual edits made via external editors and ensures that only valid configurations are applied.

## Functional Requirements
- **Manual Trigger**: A "Reload Configuration" menu item will be added to the tray icon menu under `Settings`, directly below "Open Configuration File".
- **Atomic Reload**: The application will read the `config.toml` file, validate its structure and content (using existing Pydantic models), and update the live configuration instance.
- **Validation & Error Handling**:
    - If the file is valid, the new settings are applied immediately to all active components (hotkeys, providers, etc.).
    - If the file is invalid (syntax error or validation failure), the application will NOT apply the changes and will continue using the previous valid configuration.
- **User Feedback**:
    - **Success**: Upon a successful reload, the tray icon tooltip will briefly change to "ParrotInk: Config Updated" (or similar) to confirm the action.
    - **Failure**: If validation fails, a standard Windows message box will appear showing the specific error details so the user can correct the file.

## Non-Functional Requirements
- **Thread Safety**: The reload operation must be thread-safe and not block the main application loop or the UI thread excessively.
- **Robustness**: The application must remain stable even if the configuration file is deleted or corrupted during the reload attempt.

## Acceptance Criteria
- [ ] "Reload Configuration" item appears in the Settings menu.
- [ ] Clicking "Reload Configuration" successfully updates the hotkey if changed in the file.
- [ ] Clicking "Reload Configuration" successfully updates the provider if changed in the file.
- [ ] An invalid TOML file triggers a Windows message box error and doesn't crash the app.
- [ ] Success is indicated via a tooltip update.

## Out of Scope
- Automatic file watching (hot-reloading without user interaction).
- GUI-based configuration editor (beyond the existing tray toggles).
