# Implementation Plan: Windows-Native Background Update Manager

## Phase 1: Update Service Enhancement
- [ ] Task: Enhance `GitHubClient` to extract asset URLs (`engine/services/updates.py`)
    - [ ] Update `fetch_latest_release` to return `browser_download_url` for `ParrotInk-Setup.exe` and `ParrotInk-Setup.exe.sha256`.
- [ ] Task: Implement `DownloadService` using PowerShell BITS
    - [ ] Add `start_bits_download(url, dest)` to `engine/services/updates.py`.
    - [ ] Add `get_bits_status()` to monitor the download percentage and job state.
    - [ ] Use `Complete-BitsTransfer` to finalize the download once it reaches the "Transferred" state.
- [ ] Task: Implement `ChecksumVerifier`
    - [ ] Add a utility function to compute the SHA256 of the downloaded file and compare it against the content of the `.sha256` asset.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Update Service Enhancement' (Protocol in workflow.md)

## Phase 2: Lifecycle & UI Integration
- [ ] Task: Update `UpdateManager` to handle states
    - [ ] Manage states: `IDLE`, `CHECKING`, `DOWNLOADING`, `READY_TO_INSTALL`.
    - [ ] Automatically start the BITS download in the background when an update is found.
    - [ ] Poll BITS status periodically and update the UI bridge.
- [ ] Task: Update `TrayApp` and `ui_bridge` for dynamic menu labels
    - [ ] Update the tray menu's top version label to show `Downloading Update (X%)` or `Install Update (Ready)`.
    - [ ] Add the callback to launch the installer and exit the app when `Install Update (Ready)` is clicked.
- [ ] Task: Integrate Windows Toast Notifications
    - [ ] Trigger a notification when the download is complete and verified.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Lifecycle & UI Integration' (Protocol in workflow.md)

## Phase 3: Robustness & Cleanup
- [ ] Task: Implement error handling for BITS failures
    - [ ] Revert to `Update Available` if the BITS job fails or is cancelled by the system.
- [ ] Task: Ensure clean temporary file management
    - [ ] Use `tempfile` for installer storage and ensure old versions are cleaned up.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Robustness & Cleanup' (Protocol in workflow.md)
