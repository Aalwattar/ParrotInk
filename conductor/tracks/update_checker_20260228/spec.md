# Specification: GitHub Update Checker

## 1. Overview
Implement a non-intrusive update checking system that compares the current application version against the latest release available on GitHub.

## 2. Functional Requirements
- **Update Checking:**
    - The application must automatically check for updates once at startup.
    - Subsequent checks must occur every 24 hours if the application remains running.
    - Use the GitHub REST API (`/repos/Aalwattar/ParrotInk/releases/latest`) to fetch the latest version.
    - Handle `404` (No Releases) and `403` (Rate Limited) as "No Update Available" states without excessive logging.
- **UI Feedback:**
    - If an update is available (remote version > local version), the tray menu's version label should be updated to include a notification.
    - **UI implementation:** The version label must be implemented as a clickable menu item (not a disabled label) to ensure callback support.
    - Example: `v0.1.5` becomes `v0.1.5 (Update Available)`.
- **User Action:**
    - Clicking the modified version label must open the default web browser to the GitHub releases page.

## 3. Architecture & Isolation
- **UpdateManager Service:** Create a standalone `UpdateManager` (e.g., in `engine/services/updates.py`).
- **Threading:** All network I/O and JSON parsing **MUST** run in a dedicated background thread to prevent UI freezes.
- **Versioning:** Use the `packaging.version` library for all comparisons to correctly handle pre-releases (rc), post-releases, and complex tags.
- **UI Bridge:** The `UpdateManager` should signal the `AppCoordinator`, which will then trigger the UI refresh on the appropriate thread.
- **Rate Limiting:** Proactively check `X-RateLimit-Remaining` headers to avoid 403 blocks.

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
