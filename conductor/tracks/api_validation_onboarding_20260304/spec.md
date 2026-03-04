# Specification: API Key Validation & Onboarding

## Goal
Prevent the application from attempting connections with invalid or missing API keys, especially on first launch. Improve onboarding by showing instructions in the HUD if a user tries to use a hotkey before configuring a key.

## Problem Statement
- Application attempts to connect with placeholder keys (like "4444") or empty keys.
- Resulting log errors are noisy and confusing for new users.
- Menu items and connection logic should be gated by valid configuration.

## Proposed Changes
1.  **Gated Connections**:
    -   Modify the connection logic to check if the active provider's API key is valid (not empty and not a placeholder like "4444").
    -   Disable the "Start Session" / "Connect" menu items in the tray if no valid key is present.
2.  **HUD Onboarding**:
    -   If the user presses the hotkey while the API key is missing, instead of attempting a connection that will fail, show a clear instructional message in the HUD: "API Key Required. Open Tray Menu > Settings to add it."
3.  **Config Validation**:
    -   Ensure the default config doesn't use placeholders that look "real" enough to trigger connection attempts.

## Success Criteria
- No "Invalid API Key" errors in logs on first launch.
- Tray menu "Start" item is disabled when no key is set.
- Hotkey press with no key shows onboarding message in HUD.
