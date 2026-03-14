# Implementation Plan: Inno Setup Installer & Automated Releases

## Phase 1: Inno Setup Script Development
- [x] Task: Create initial Inno Setup script (`packaging/inno/parrotink.iss`) [6e15263]
    - [x] Define application metadata (Name, Version, Publisher).
    - [x] Configure `DefaultDirName` to use `%LOCALAPPDATA%\ParrotInk` (`{userappdata}`).
    - [x] Set `PrivilegesRequired=lowest` to prevent UAC prompts.
    - [x] Include the primary executable (`ParrotInk.exe`) and icon assets in the `[Files]` section.
    - [x] Define Start Menu and Desktop shortcuts in the `[Icons]` section.
- [x] Task: Implement smart update and process management in the ISS [6e15263]
    - [x] Add `[Code]` section to use `FindWindowByWindowName` or `psvince` plugin to detect a running instance.
    - [x] Alternatively, use `AppMutex` if the application creates one, or simple command-line `taskkill` via `[Run]` before install.
    - [x] Configure `[UninstallDelete]` to cleanly remove binary directories while leaving configuration in `%APPDATA%` untouched.
    - [x] Add post-install run configuration to automatically launch `ParrotInk.exe` after a successful install.
- [x] Task: Local Build Verification [6e15263]
    - [x] Test compiling the script locally using Inno Setup Compiler.
    - [x] Verify the installer correctly stops a running instance, updates files, and relaunches.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Inno Setup Script Development' (Protocol in workflow.md) [6e15263]

## Phase 2: GitHub Actions Automation
- [x] Task: Update the `release.yml` GitHub Actions workflow [5bf86f1]
    - [x] Add a step to download and install Inno Setup (e.g., using `innosetup-action` or a `choco install` step).
    - [x] Add a step to compile the `parrotink.iss` script using `iscc` in headless mode.
    - [x] Update the `Compute checksum` step to generate hashes for both `ParrotInk.exe` and `ParrotInk-Setup.exe`.
    - [x] Update the `Create GitHub Release + upload assets` step to include all four artifacts: `ParrotInk-Setup.exe`, `ParrotInk-Setup.exe.sha256`, `ParrotInk.exe`, `ParrotInk.exe.sha256`.
- [x] Task: Conductor - User Manual Verification 'Phase 2: GitHub Actions Automation' (Protocol in workflow.md) [5bf86f1]

## Phase 3: Documentation
- [x] Task: Update `README.md` [84e2ffe]
    - [x] Overhaul the "Installation" section to prominently feature the `ParrotInk-Setup.exe`.
    - [x] Move the standalone executable instructions to a secondary section or note, explicitly warning against its use for standard installations (especially regarding Windows Startup path stability).
- [x] Task: Conductor - User Manual Verification 'Phase 3: Documentation' (Protocol in workflow.md) [84e2ffe]

## Phase: Review Fixes
- [x] Task: Apply review suggestions [33f6868]
