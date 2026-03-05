# Specification: Config Fidelity & Audio Privacy UX Improvements

## Goal
Resolve two major regressions:
1. Prevent the application from stripping comments when saving `config.toml` by utilizing a style-preserving TOML library.
2. Enhance the user experience and visibility when Windows Privacy settings block microphone access by providing clear, actionable popups, ensuring HUD messages persist, and halting network connections to prevent log spam.

## Problem Statement
- **Config Overwrite:** When the application saves state changes (e.g., a hotkey change) via `tomli_w`, it writes a purely structural TOML file, completely stripping away the helpful documentation and comments provided in `config.example.toml`.
- **Silent Mid-Session Mic Block:** If the microphone is blocked by OS privacy settings while the app is running, the tray menu and UI do not immediately reflect the error state (requiring an app restart to see the "🚨 FIX" link). Furthermore, the application still attempts to connect to providers (resulting in timeout log loops).
- **Transient UI:** The HUD error message disappears too quickly, and the user lacks an unmissable, clear call-to-action on the screen. The descriptive text also points to an outdated Windows 10 settings path.

## Proposed Changes
1. **Config Preservation:**
    - Replace the standard `tomli_w` dump mechanism in `engine/config.py` with a style-preserving library (such as `tomlkit`).
    - Ensure inline comments, spacing, and the original structure of `config.toml` are maintained when saving state programmatically.
2. **Dynamic Diagnostic & Pipeline Guard:**
    - Modify `main.py` to explicitly halt any attempts to connect to OpenAI or AssemblyAI (preventing network timeouts and log spam) if the local OS-level microphone diagnostic indicates a hardware or privacy block.
    - Ensure the diagnostic runs reliably on every "Start Listening" trigger so the Tray UI and App State dynamically update with the "🚨 FIX" link immediately, even if the privacy permission was revoked mid-session (without requiring an app restart).
3. **Enhanced Privacy UI:**
    - **Actionable Popup Dialog:** Trigger a styled popup dialog (using `ttkbootstrap` or a native `win11toast` with buttons) displaying a clear description of the privacy block and an action to take the user directly to the "Privacy & security > Microphone" Windows settings page.
    - **Persistent HUD:** Adjust the HUD timeout logic so that when a severe hardware error (like a privacy block) is detected, the error message remains visible on the screen until the user acknowledges it or the hardware state changes.
    - **Updated Copy:** Update the instruction text to specifically reference the Windows 11 path: "Privacy & security > Microphone".

## Success Criteria
- Editing the configuration via the app (or toggling settings in the tray) updates `config.toml` while perfectly preserving all original comments and structure.
- Blocking microphone access mid-session and triggering the hotkey immediately halts network connection attempts and updates the Tray menu with the Fix link without an app restart.
- A persistent error message appears in the HUD when the mic is blocked.
- A clear, styled popup appears explaining the issue with a direct link/button to the correct Windows 11 Privacy settings page.
