# Specification: Fix "DLL Not Found" and Environment Poisoning during Handoff

## Problem Statement
When upgrading ParrotInk via the Tray Icon menu, the application often fails to restart, showing a "python.dll not found" error. This is a regression that has persisted through multiple "fix" attempts involving time delays.

Manual installation (running the installer from Explorer) always works, indicating that the issue is specific to the handoff from the frozen parent process to the installer.

## Root Cause Analysis
1.  **DLL Search Path Inheritance:** PyInstaller `--onefile` apps modify the Windows DLL search path (via `SetDllDirectoryW`) to point into a temporary `_MEIxxxx` directory. This search path is inherited by child processes (the installer) and grandchild processes (the new version of the app). The new version then tries to load its DLLs from the *old* and potentially deleted/locked directory.
2.  **Environment Poisoning:** Inherited environment variables like `_MEIPASS` can confuse the PyInstaller bootloader of the new version.
3.  **Incomplete Handoff:** A `NameError` in `engine/gui_main.py` is currently breaking the update handoff callback, leading to unstable exits.
4.  **Brutal Shutdowns:** The current installer logic uses `taskkill /f` as a primary fallback, which prevents clean `_MEI` directory cleanup.

## Requirements
### P0: Logic Integrity
*   Fix the `NameError: os is not defined` in `engine/gui_main.py` to ensure the update trigger is stable.

### P1: Environmental Sanitization (Python)
*   Reset the Windows DLL search path using `ctypes.windll.kernel32.SetDllDirectoryW(None)` before launching the installer.
*   Scrub the system `PATH` of any entries derived from `sys._MEIPASS`.
*   Clear the `_MEIPASS` environment variable.
*   Set `PYINSTALLER_RESET_ENVIRONMENT = "1"` to signal a clean boot for the new version.
*   Use `ShellExecuteW` to launch the installer to ensure proper UAC elevation and process decoupling.

### P2: Deterministic Installer Logic (Inno Setup)
*   Modify `InitializeSetup` to treat a missing PID as success (process already exited).
*   Remove the non-deterministic `taskkill /f` fallback for PID wait failures.
*   Implement `runasoriginaluser` in the `[Run]` section to prevent the app from launching with admin privileges.

### P3: Architectural Debt (TODO)
*   **Transition to `--onedir`**: Plan the migration from a single-file executable to a directory-based one to eliminate the `%TEMP%` extraction layer entirely.

## Success Criteria
1.  In-app updates via the Tray Icon no longer result in "DLL not found" errors.
2.  The update handoff no longer crashes with `NameError`.
3.  The application restarts with the correct user permissions (non-admin).
4.  The installer correctly identifies when the parent process has exited without force-killing it.
