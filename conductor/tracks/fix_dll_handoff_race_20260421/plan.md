# Implementation Plan: Fix "DLL Not Found" Handoff Race

## Step 0: Fix Handoff Crash (P0)
- [x] Investigate `engine/gui_main.py` and fix the `NameError: name 'os' is not defined` inside the update callback.
- [x] Verify fix by running a mock update check (if possible) or dry-run.

## Step 1: Sanitize Environment for Installer (P1)
- [x] Implement `sanitize_for_external_process()` in `engine/services/updates.py`.
    - [x] Reset DLL search path via `SetDllDirectoryW(None)`.
    - [x] Scrub `PATH` of `_MEIPASS` relative paths.
    - [x] Set `PYINSTALLER_RESET_ENVIRONMENT=1`.
- [x] Update `UpdateManager.install_now()` to use `ctypes.windll.shell32.ShellExecuteW`.
- [x] Verify that the installer launches correctly with the sanitized environment.

## Step 2: Deterministic Installer Cleanup (P2)
- [x] Update `packaging/inno/parrotink.iss`.
    - [x] Refactor `InitializeSetup` to handle `OpenProcess` failure as "already exited" success.
    - [x] Remove `taskkill /f` fallback logic.
    - [x] Update `[Run]` section with `runasoriginaluser`.
- [x] Rebuild the installer and verify the shutdown logic.

## Step 3: Architectural Refactoring (P3)
- [ ] TODO: Transition PyInstaller build from `--onefile` to `--onedir`.

## Verification Tasks
- [x] Perform a full end-to-end upgrade from a previous version to the current one via the Tray Icon.
- [x] Verify that the application restarts without "DLL not found" errors.
- [x] Verify that the application is not running as Administrator after the update.
- [x] Inspect the installer log (`%TEMP%\Setup Log...`) to confirm `OpenProcess` behavior.
