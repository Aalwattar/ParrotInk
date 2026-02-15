# Specification: fix_hotkey_connection_20260215

## Overview
This track addresses two regressions identified after recent changes:
1.  **Hotkey Misfire:** Pressing `Ctrl+Alt` alone triggers the recording start sound/HUD, even though the configured hotkey is `Ctrl+Alt+V`. This indicates a flaw in the partial match logic or "Any Key" monitoring.
2.  **AssemblyAI Connection Timeout:** The application throws a `TimeoutError` / `CancelledError` when connecting to AssemblyAI if the connection takes exactly 10 seconds (the default timeout).

## Functional Requirements
1.  **Strict Hotkey Matching:** The application must ONLY trigger `start_listening` when the *exact* hotkey combination (e.g., `Ctrl+Alt+V`) is pressed. Partial matches (e.g., `Ctrl+Alt`) must be ignored.
2.  **Robust AssemblyAI Connection:**
    *   Increase the connection timeout for AssemblyAI to accommodate slower handshakes (e.g., 20 seconds).
    *   Implement a retry mechanism or better error handling for `CancelledError` during connection.

## Non-Functional Requirements
- **Responsiveness:** Hotkey detection must remain fast.
- **Stability:** Connection failures should gracefully degrade or retry without crashing the main loop.

## Acceptance Criteria
- [ ] Pressing `Ctrl+Alt` (without `V`) does NOT trigger the HUD or start sound.
- [ ] Pressing `Ctrl+Alt+V` correctly toggles recording.
- [ ] AssemblyAI connection succeeds even if it takes >10s (up to 20s).
- [ ] Explicit `TimeoutError` is logged if connection fails, rather than a generic traceback.
