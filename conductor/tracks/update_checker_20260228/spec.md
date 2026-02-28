# Specification: GitHub Update Checker

## 1. Overview
Implement a non-intrusive update checking system that compares the current application version against the latest release available on GitHub.

## 2. Functional Requirements
- **Update Checking:**
    - The application must automatically check for updates once at startup.
    - Subsequent checks must occur every 24 hours if the application remains running.
    - Use the GitHub REST API (`/repos/Aalwattar/ParrotInk/releases/latest`) to fetch the latest version.
- **UI Feedback:**
    - If an update is available (remote version > local version), the tray menu's version label should be updated to include a notification.
    - Example: `v0.1.5` becomes `v0.1.5 (Update Available)`.
- **User Action:**
    - Clicking the modified version label must open the default web browser to the GitHub releases page for `ParrotInk`.

## 3. Architecture & Isolation
- **UpdateManager Service:** Create a standalone `UpdateManager` (e.g., in `engine/services/updates.py`) to handle fetching, parsing, and state management.
- **UI Integration:** The `UpdateManager` should notify the `TrayIcon` (via a signal or callback) to refresh the menu label when a new version is detected.
- **Error Handling:** Gracefully handle network failures or GitHub rate-limiting without interrupting the main application logic.

## 4. Non-Functional Requirements
- **Rate Limit Safety:** Ensure unauthenticated API calls do not exceed GitHub's hourly limits.
- **Privacy:** No user-identifiable data should be sent in the request header.

## 5. Acceptance Criteria
- [ ] Application checks GitHub once on launch.
- [ ] Tray menu reflects update status if a newer version exists.
- [ ] Clicking the update label opens the correct browser URL.
- [ ] No performance impact on audio processing or hotkey logic.

## 6. Out of Scope
- Automated downloads or silent background installations.
- Beta/Pre-release channel selection (production releases only).
