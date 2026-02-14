# Specification: Run at Startup Feature

## 1. Overview
This track adds a "Run at Startup" feature to Voice2Text, allowing the application to automatically launch when the user logs into Windows. The configuration file remains the source of truth, while a **Registry Value** under the Windows `Run` key is used to implement the actual startup behavior.

## 2. Functional Requirements

### 2.1 Configuration
- Add a new configuration key: `interaction.run_at_startup` (boolean, default: `false`).
- This key serves as the authoritative source of truth for the feature.

### 2.2 System Integration (Windows Registry)
- Implement logic to manage the Windows Registry **Value** named "Voice2Text" under the key: `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`.
- **Startup Sync:** On application launch, if `run_at_startup` is `true` in the config, the application must ensure the registry value exists and points to the current executable's path. This handles cases where the application has been moved.
- **Toggle Logic:** When the setting is toggled via the UI:
    1. Update the configuration value in `config.toml`.
    2. Trigger an immediate sync to create/update or remove the registry value based on the new config state.

### 2.3 User Interface (System Tray)
- Add a new menu item to the "Settings" sub-menu in the system tray.
- **Label:** "Run at Startup".
- **Interaction:** A simple checkbox/toggle.
- The UI must reflect the state of the configuration file.

## 3. Technical Requirements
- **Module:** All registry manipulation logic must be isolated in a new file: `engine/platform_win/startup.py`.
- **API:** Use `winreg` (standard Python library) for registry access.
- **Portability:** Ensure the logic correctly identifies the executable path whether running as a Python script or a compiled `.exe` (using `sys.executable` or `sys.argv[0]`).

## 4. Acceptance Criteria
- [ ] Toggling "Run at Startup" in the tray menu correctly updates `config.toml`.
- [ ] Enabling the feature creates the "Voice2Text" **value** in the Windows Startup registry.
- [ ] Disabling the feature removes the "Voice2Text" **value** from the registry.
- [ ] Moving the executable and launching it (if enabled) correctly updates the registry path to the new location.
- [ ] The feature works correctly for both the source-code version and the compiled standalone executable.

## 5. Out of Scope
- Support for non-Windows operating systems.
