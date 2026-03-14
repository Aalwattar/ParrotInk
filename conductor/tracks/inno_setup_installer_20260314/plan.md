# Implementation Plan: Inno Setup Installer & Automated Releases

## Phase 1: Inno Setup Script Development
- [ ] Task: Create initial Inno Setup script (`packaging/inno/parrotink.iss`)
    - [ ] Define application metadata (Name, Version, Publisher).
    - [ ] Configure `DefaultDirName` to use `%LOCALAPPDATA%\ParrotInk` (`{userappdata}`).
    - [ ] Set `PrivilegesRequired=lowest` to prevent UAC prompts.
    - [ ] Include the primary executable (`ParrotInk.exe`) and icon assets in the `[Files]` section.
    - [ ] Define Start Menu and Desktop shortcuts in the `[Icons]` section.
- [ ] Task: Implement smart update and process management in the ISS
    - [ ] Add `[Code]` section to use `FindWindowByWindowName` or `psvince` plugin to detect a running instance.
    - [ ] Alternatively, use `AppMutex` if the application creates one, or simple command-line `taskkill` via `[Run]` before install.
    - [ ] Configure `[UninstallDelete]` to cleanly remove binary directories while leaving configuration in `%APPDATA%` untouched.
    - [ ] Add post-install run configuration to automatically launch `ParrotInk.exe` after a successful install.
- [ ] Task: Local Build Verification
    - [ ] Test compiling the script locally using Inno Setup Compiler.
    - [ ] Verify the installer correctly stops a running instance, updates files, and relaunches.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Inno Setup Script Development' (Protocol in workflow.md)

## Phase 2: GitHub Actions Automation
- [ ] Task: Update the `release.yml` GitHub Actions workflow
    - [ ] Add a step to download and install Inno Setup (e.g., using `innosetup-action` or a `choco install` step).
    - [ ] Add a step to compile the `parrotink.iss` script using `iscc` in headless mode.
    - [ ] Update the `Compute checksum` step to generate hashes for both `ParrotInk.exe` and `ParrotInk-Setup.exe`.
    - [ ] Update the `Create GitHub Release + upload assets` step to include all four artifacts: `ParrotInk-Setup.exe`, `ParrotInk-Setup.exe.sha256`, `ParrotInk.exe`, `ParrotInk.exe.sha256`.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: GitHub Actions Automation' (Protocol in workflow.md)

## Phase 3: Documentation
- [ ] Task: Update `README.md`
    - [ ] Overhaul the "Installation" section to prominently feature the `ParrotInk-Setup.exe`.
    - [ ] Move the standalone executable instructions to a secondary section or note, explicitly warning against its use for standard installations (especially regarding Windows Startup path stability).
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Documentation' (Protocol in workflow.md)
