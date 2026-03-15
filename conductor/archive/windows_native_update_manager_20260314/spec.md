# Specification: Windows-Native Background Update Manager

## Overview
This track implements a professional, background-driven update system for ParrotInk. It leverages the Windows Background Intelligent Transfer Service (BITS) via PowerShell to download updates silently and efficiently, ensuring a robust user experience that survives network interruptions and application restarts.

## Functional Requirements
1. **Background Discovery (Existing Logic Enhancement)**:
    - The existing `UpdateManager` (in `engine/services/updates.py`) will be enhanced.
    - It currently checks for updates via the GitHub API. It will be updated to also extract the `browser_download_url` for the `ParrotInk-Setup.exe` and its corresponding `.sha256` checksum file.

2. **Silent Background Download (BITS)**:
    - When an update is detected, the app will automatically initiate a background download using PowerShell's `Start-BitsTransfer` cmdlet.
    - **Efficiency**: BITS will be used in "Asynchronous" mode, allowing it to download only during idle bandwidth periods.
    - **Persistence**: The download will persist even if ParrotInk is closed or the system is rebooted.

3. **Status Monitoring & UI Integration**:
    - The `UpdateManager` will monitor the BITS job status.
    - **Tray Menu**: While downloading, the top menu item will display `Downloading Update (X%)`.
    - **Completion**: Once the download is 100% complete and verified (see below), the top menu item will change to `Install Update (Ready)`.
    - **Notification**: A native Windows Toast notification will inform the user once the update is ready for installation.

4. **Security & Verification**:
    - Before prompting for installation, the app must download the `.sha256` file from the release.
    - The app will verify the downloaded `ParrotInk-Setup.exe` against the hash to ensure file integrity and security.

5. **User-Controlled Installation**:
    - The app will **not** force an update.
    - Clicking `Install Update (Ready)` will prompt the user: "ParrotInk will now close to run the installer. Re-launch manually after setup." (The installer itself will offer to auto-launch the app).
    - Upon confirmation, the app will launch the verified installer from the `%TEMP%` directory and exit gracefully.

## Acceptance Criteria
- [ ] New versions are detected, and the setup EXE URL is correctly identified.
- [ ] Downloads start automatically and silently in the background using BITS.
- [ ] The tray menu accurately reflects the download percentage.
- [ ] A toast notification appears only after a successful and verified download.
- [ ] The app verifies the SHA256 checksum before allowing the user to launch the installer.
- [ ] Launching the installer correctly closes the app and starts the setup process.

## Out of Scope
- Implementing a custom "downloader" UI window (UI is restricted to Tray and Toasts).
- Auto-updating without user consent (user must always click "Install").
