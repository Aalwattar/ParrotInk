# Specification: Cancel Dictation on Click Outside Anchor

## 1. Overview
This feature enhances the dictation UX by mimicking the "Win+H" behavior: if the user clicks away from the target application or control while dictation is active, the session should automatically cancel. However, clicking *within* the active target (anchor) should maintain the session. This prevents accidental text injection into unintended windows and provides a more natural way to stop dictation.

## 2. Functional Requirements

### 2.1 Anchor Capture
- **Trigger:** When dictation becomes `ACTIVE` (starts listening), the system must capture an "Anchor" representing the target context.
- **Anchor Definition:**
  - **Control Scope:** The specific UI Automation element (focused control/widget).
  - **Window Scope:** The foreground window handle (HWND).
- **Configuration:** The scope is determined by the `anchor_scope` configuration setting.

### 2.2 Mouse Interaction Handling
- **Event:** Monitor global **Left Mouse Click** events while the dictation session is `ACTIVE`.
- **Constraint:** Do **not** block or interfere with Right-clicks, Middle-clicks, Scrolling, or Mouse Movement. These should function normally.
- **Logic:**
  1.  **On Left Click:** Determine the target element/window under the mouse cursor.
  2.  **Comparison:** Compare the click target with the captured Anchor.
  3.  **Outcome:**
      -   **Match (Inside Anchor):** Ignore the click event (let it pass through) and **continue** dictation.
      -   **Mismatch (Outside Anchor):** **Stop** the dictation session immediately.
- **Restriction:** Mouse clicks must **never** trigger the *start* of a dictation session.

### 2.3 Configuration
- Introduce a new configuration section (or add to existing `interaction` config):
  ```toml
  [interaction]
  # Enable/Disable the feature
  cancel_on_click_outside_anchor = true

  # Scope of the anchor: "control" (default) or "window"
  anchor_scope = "control"
  ```
  - `control`: Uses UI Automation to track the specific text box or control.
  - `window`: Uses the window handle (HWND) to track the main application window.
  - **Fallback:** If `anchor_scope = "control"` but a specific control cannot be resolved, fallback to "window" scope.

### 2.4 User Feedback
- **Cancellation:** When dictation is stopped via click-away, the system tray icon must update from "Recording" to "Idle" (Visual Feedback).
- **No Audio:** No specific sound effect is required for this cancellation event (consistent with manual stop).

## 3. Non-Functional Requirements
- **Performance:** The global mouse hook must be lightweight and not introduce perceptible lag to cursor movement or clicking.
- **Stability:** The hook must be robust; if the anchor window is closed, the session should gracefully stop.
- **Security:** Ensure UI Automation does not expose sensitive data beyond the necessary handles/IDs for comparison.

## 4. Acceptance Criteria
1.  **Config Configured:** User can set `anchor_scope` to "window" or "control" in `config.toml`.
2.  **Window Anchor:** With `anchor_scope = "window"`, clicking anywhere inside the active Notepad window keeps dictation running. Clicking on the Desktop or another app stops it.
3.  **Control Anchor:** With `anchor_scope = "control"`, clicking inside the specific text area keeps dictation running. Clicking the window title bar or a different sidebar in the same app stops it.
4.  **Passthrough:** Right-clicks and scrolling work normally without stopping dictation (unless they also change focus, which is OS-dependent, but our logic targets Left Click).
5.  **Visual Feedback:** The tray icon correctly reverts to the idle state upon cancellation.
