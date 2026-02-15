# Specification: fix_hotkey_connection_20260215

## Overview
Users are reporting two regression issues:
1.  **Hotkey Misfire:** Partial hotkey presses (e.g., `Ctrl+Alt`) sometimes trigger the recording state, HUD, and sound, despite the configured hotkey being `Ctrl+Alt+V`. This suggests a flaw in the key matching logic.
2.  **Systemic Connection Latency:** Both OpenAI (disconnection) and AssemblyAI (connection) are exhibiting abnormal delays (>10-20s). This suggests a potential root cause in the application's networking or event loop handling that needs investigation.

## Functional Requirements
1.  **Strict Hotkey Matching:** The application must ONLY trigger `start_listening` when the *exact* hotkey combination is pressed. Partial matches must be ignored.
2.  **Generalized Robust Networking:**
    *   **Universal Timeout:** The 2-second disconnection timeout strategy must be applied to the abstract `BaseProvider` to ensure all current and future providers exit cleanly without hanging.
    *   **Retry Logic:** `ConnectionManager` must implement an automatic retry mechanism (e.g., 3 attempts with exponential backoff) for initial connections.
    *   **Extended Timeout:** Increase the default connection timeout to 20 seconds to accommodate slower network conditions.
3.  **Responsive Feedback:** The UI (Tray and HUD) must display "Connecting..." or "Disconnecting..." states immediately and must not freeze during these operations.

## Non-Functional Requirements
- **Architecture:** Network timeouts and retry policies must be implemented at the `ConnectionManager` or `BaseProvider` level, not hardcoded into specific provider implementations.
- **Diagnostics:** The application should log detailed timing information for connection/disconnection events to aid in diagnosing the root cause of the latency.

## Acceptance Criteria
- [ ] Pressing `Ctrl+Alt` (without `V`) never triggers the HUD or start sound.
- [ ] Switching from any provider to any other provider completes (visually) instantly.
- [ ] If a provider fails to connect on the first attempt, it retries automatically up to 3 times before showing an error.
- [ ] Disconnection of *any* provider is forcibly capped at 2 seconds.
- [ ] Logs show clear timestamps for "Start Connect", "Connected", "Start Disconnect", and "Disconnected".
