# Specification: Inno Setup Installer & Automated Releases

## Overview
The goal of this track is to create a robust, professional installer for ParrotInk using Inno Setup. This installer will encapsulate the existing single-file executable (`ParrotInk.exe`) and provide a seamless installation and update experience for users. The build and distribution of this installer must be fully automated via GitHub Actions, and the project documentation must be updated to strongly recommend the installer over the portable version.

## Functional Requirements
1. **Inno Setup Script (`packaging/inno/parrotink.iss`)**:
    - **Branding**: Must display the correct application name ("ParrotInk"), version, and publisher information.
    - **Iconography**: Must use the existing high-quality `.ico` assets for the installer executable and created shortcuts.
    - **Install Location**: Default installation directory must be `%LOCALAPPDATA%\ParrotInk` to allow installation without requiring Administrator privileges (UAC).
    - **Shortcuts**: Must automatically create a Desktop shortcut and a Start Menu program group entry.
    - **Payload**: Must bundle the `ParrotInk.exe` build output and any required external assets (if they are not already baked into the PyInstaller payload).
2. **Smart Update & Lifecycle Management**:
    - **Pre-Install Process Check**: The installer must detect if `ParrotInk.exe` is currently running and force-stop/kill the process to prevent file-in-use errors.
    - **Clean Upgrade**: When installing over an existing version, the installer must cleanly uninstall the old version (removing old binaries) before laying down the new files.
    - **Post-Install Action**: The installer must offer to (or automatically) launch ParrotInk after a successful installation/update.
    - **Uninstall Process**: A clean uninstaller must be provided that removes the application directory and shortcuts (user configuration in `%APPDATA%` should ideally be preserved or prompted).
3. **GitHub Actions Automation**:
    - Modify the existing release workflow (`.github/workflows/release.yml`) to run the Inno Setup compiler (`iscc`) in headless mode after the PyInstaller build completes.
    - **Release Assets**: The automated release must upload the following artifacts:
        - `ParrotInk-Setup.exe` (The Installer)
        - `ParrotInk-Setup.exe.sha256` (Installer Checksum)
        - `ParrotInk.exe` (The Portable Executable)
        - `ParrotInk.exe.sha256` (Portable Executable Checksum)
4. **Documentation Updates**:
    - **README.md**: Overhaul the installation section to strongly push the `ParrotInk-Setup.exe` as the primary and recommended method.
    - The portable `ParrotInk.exe` must be explicitly labeled as an option for "advanced users or temporary use only," noting potential issues with Windows Startup registration if the file is moved.

## Acceptance Criteria
- [ ] Running the generated `ParrotInk-Setup.exe` successfully installs the application to `%LOCALAPPDATA%\ParrotInk`.
- [ ] The installer correctly identifies a running instance of ParrotInk, stops it, and updates the application without errors.
- [ ] The uninstaller removes the executable and shortcuts cleanly.
- [ ] A triggered GitHub Release successfully builds and attaches all four required assets (Installer, Portable EXE, and both checksums).
- [ ] The README clearly steers general users toward the installer.

## Out of Scope
- Modifying the core `ParrotInk.exe` functionality or PyInstaller configuration (beyond ensuring compatibility with the installer wrapper).
- Implementing an in-app auto-updater (the update process assumes the user downloads and runs the new installer).
