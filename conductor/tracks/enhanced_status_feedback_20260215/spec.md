# Specification: enhanced_status_feedback_20260215

## Overview
Improve the application's transparency during long-running or fragile operations like connecting to an API or switching providers. Instead of silent waits or hiding the UI, the application will provide detailed, real-time status updates through the HUD and the system tray tooltip.

## Functional Requirements
1.  **Detailed Status Messaging:**
    *   Implement a mechanism to pass arbitrary status strings from the engine to the UI.
    *   Example messages: "Connecting to OpenAI...", "Retry 2/3 (Timeout)...", "Switching to AssemblyAI...".
2.  **HUD Integration:**
    *   The HUD must display the current status message prominently during the `CONNECTING` or `SWITCHING` states.
    *   Transition smoothly from "DISCONNECTING" -> "CONNECTING" -> "LISTENING".
3.  **Tray Tooltip Updates:**
    *   The tray icon's tooltip (title) should reflect the current detailed status (e.g., "Voice2Text: Connecting...").
4.  **Optimized Provider Switching:**
    *   Refactor the provider switch logic to keep the HUD visible and show a "Switching..." message instead of immediately hiding it.

## Non-Functional Requirements
- **Thread Safety:** Status updates must be passed through the existing thread-safe `UIBridge`.
- **Decoupling:** The engine should not know about the UI implementation details, only that it is sending a "Status Update" signal.

## Acceptance Criteria
- [ ] Clicking a new provider in the tray shows "Switching to [Provider]..." on the HUD immediately.
- [ ] During connection retries, the HUD and Tray Tooltip show "Retry [X]/3...".
- [ ] On successful connection, the HUD transitions to its standard listening state.
- [ ] On connection failure, the tray tooltip shows the last error summary.
- [ ] No UI freezing or "frozen" HUD states during transitions.
