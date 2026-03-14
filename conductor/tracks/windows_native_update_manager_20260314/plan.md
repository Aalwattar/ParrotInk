# Implementation Plan: Windows-Native Background Update Manager

## Phase 1: Update Service Enhancement
- [x] Task: Enhance `GitHubClient` to extract asset URLs (`engine/services/updates.py`) [2aecfc5]
    - [x] Update `fetch_latest_release` to return `browser_download_url` for `ParrotInk-Setup.exe` and `ParrotInk-Setup.exe.sha256`.
- [x] Task: Implement `DownloadService` using PowerShell BITS [2ae098c]
    - [x] Add `start_bits_download(url, dest)` to `engine/services/updates.py`.
    - [x] Add `get_bits_status()` to monitor the download percentage and job state.
    - [x] Use `Complete-BitsTransfer` to finalize the download once it reaches the "Transferred" state.
- [x] Task: Implement `ChecksumVerifier` [2ae098c]
    - [x] Add a utility function to compute the SHA256 of the downloaded file and compare it against the content of the `.sha256` asset.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Update Service Enhancement' (Protocol in workflow.md) [2ae098c]

## Phase 2: Lifecycle & UI Integration
- [x] Task: Update `UpdateManager` to handle states [4c4a2bf]
    - [x] Manage states: `IDLE`, `CHECKING`, `DOWNLOADING`, `READY_TO_INSTALL`.
    - [x] Automatically start the BITS download in the background when an update is found.
    - [x] Poll BITS status periodically and update the UI bridge.
- [x] Task: Update `TrayApp` and `ui_bridge` for dynamic menu labels [b7addc6]
    - [x] Update the tray menu's top version label to show `Downloading Update (X%)` or `Install Update (Ready)`.
    - [x] Add the callback to launch the installer and exit the app when `Install Update (Ready)` is clicked.
- [x] Task: Integrate Windows Toast Notifications [b7addc6]
    - [x] Trigger a notification when the download is complete and verified.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Lifecycle & UI Integration' (Protocol in workflow.md) [b7addc6]

## Phase 3: Robustness & Cleanup
- [x] Task: Implement error handling for BITS failures [8494577]
    - [x] Revert to `Update Available` if the BITS job fails or is cancelled by the system.
- [x] Task: Ensure clean temporary file management [8494577]
    - [x] Use `tempfile` for installer storage and ensure old versions are cleaned up.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Robustness & Cleanup' (Protocol in workflow.md) [8494577]

## Phase 4: Review Fixes
- [x] Task: Apply review suggestions [c7c526d]
