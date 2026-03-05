# Specification: First-Run Onboarding Popup

## Overview
Currently, new users may not understand how to interact with the application because it operates silently in the system tray without a main window. This track introduces a "First-Run Onboarding Popup" that greets the user, explains the basic tray icon mechanics, and instructs them on how to configure their API key.

## Functional Requirements
1.  **Popup Triggering**:
    - The application must check the configuration for a specific key (e.g., `ui.show_onboarding_popup`) to determine if the popup should be displayed on startup.
    - If the application is launched with the `--background` command-line argument, the popup MUST be suppressed regardless of the configuration state.
2.  **Popup UI**:
    - The popup will be rendered using `ttkbootstrap` to maintain visual consistency with the existing configuration windows.
    - The popup must include:
        - A welcome message explaining that the app runs in the system tray.
        - Instructions stating that an API key is required.
        - Directions on how to access the Settings menu via the tray icon.
        - Directions pointing to the "Help" option in the tray menu.
    - Visuals: Include examples/images of the tray icon to aid understanding.
3.  **Dismissal Mechanism**:
    - The popup must include an interactive checkbox labeled "Don't show this again".
    - It must include an "OK" or "Close" button.
    - When dismissed, if the checkbox is checked, the application must update the configuration file (setting `ui.show_onboarding_popup = false`) so the popup does not appear on subsequent launches.

## Non-Functional Requirements
- **Consistency**: The popup must utilize the existing `ttkbootstrap` theme and `darkdetect` logic used by other UI components.
- **Fidelity**: Writing to the configuration file must preserve existing TOML comments and structure using the established `tomlkit` update logic.

## Acceptance Criteria
- [ ] On a fresh installation (or when the config flag is true), the popup appears upon launching `main.py`.
- [ ] Running `main.py --background` does *not* show the popup, even if the config flag is true.
- [ ] The popup clearly explains the tray icon, API key requirement, and Settings/Help menu locations.
- [ ] Checking the "Don't show this again" box and clicking OK successfully updates the `config.toml` file.
- [ ] Subsequent launches without the `--background` flag do *not* show the popup if the box was previously checked.

## Out of Scope
- Interactive tutorials or multi-step wizards.
- Automatic opening of the Settings window from the popup.
