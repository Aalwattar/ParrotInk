# Specification: Startup Toast Notification

## 1. Overview
Since ParrotInk runs primarily as a system tray application without a main GUI window, users may be unsure if the application has successfully started. This feature adds a native Windows toast notification upon startup to confirm the application is ready and remind the user of their configured hotkey.

## 2. Functional Requirements
- **Startup Notification:** Display a Windows toast notification when the application starts.
- **Dynamic Content:**
    - **Title:** "ParrotInk Ready"
    - **Body:** "Press {hotkey} to start transcription" (e.g., "Press CTRL+SPACE to start transcription").
- **Suppression Logic:**
    - The notification MUST NOT be shown if the application is launched with the `--background` flag (typically used for automated startup with Windows).
- **Duration:** The notification should use a "short" duration (typically 3-5 seconds).

## 3. Technical Requirements
- **Library:** Use the `win11toast` library for displaying notifications.
- **Dependency Management:** Add `win11toast` to `pyproject.toml` and update `tech-stack.md`.
- **Integration Point:** Implement the trigger in `main.py` within the standard run mode block, after configuration and single-instance checks are complete.

## 4. Acceptance Criteria
- [ ] Running `uv run python main.py` displays a toast notification with the correct title and the user's configured hotkey.
- [ ] Running `uv run python main.py --background` does NOT display a toast notification.
- [ ] The notification automatically disappears after a short duration.
- [ ] The `win11toast` library is correctly added to the project dependencies.

## 5. Out of Scope
- Interactive toast notifications (e.g., buttons inside the toast).
- Customizing the notification icon or audio at this stage.
- Notifications for other application events (e.g., error notifications, which are handled separately).
