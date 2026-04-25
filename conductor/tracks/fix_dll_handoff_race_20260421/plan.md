# Implementation Plan: Fix "DLL Not Found" Handoff Race

## Step 0: Fix Handoff Crash (P0)
- [x] 8b1a95c Investigate `engine/gui_main.py` and fix the `NameError: name 'os' is not defined` inside the update callback.
- [x] 8b1a95c Verify fix by running a mock update check (if possible) or dry-run.

## Step 1: Sanitize Environment for Installer (P1)
- [x] 8b1a95c Implement `sanitize_for_external_process()` in `engine/services/updates.py`.
    - [x] 8b1a95c Reset DLL search path via `SetDllDirectoryW(None)`.
    - [x] 8b1a95c Scrub `PATH` of `_MEIPASS` relative paths.
    - [x] 8b1a95c Set `PYINSTALLER_RESET_ENVIRONMENT=1`.
- [x] 8b1a95c Update `UpdateManager.install_now()` to use `ctypes.windll.shell32.ShellExecuteW`.
- [x] 8b1a95c Verify that the installer launches correctly with the sanitized environment.

## Step 2: Deterministic Installer Cleanup (P2) [checkpoint: a229020]
- [x] 8b1a95c Update `packaging/inno/parrotink.iss`.
    - [x] 8b1a95c Refactor `InitializeSetup` to handle `OpenProcess` failure as "already exited" success.
    - [x] 8b1a95c Remove `taskkill /f` fallback logic.
    - [x] 8b1a95c Update `[Run]` section with `runasoriginaluser`.
- [x] 8b1a95c Rebuild the installer and verify the shutdown logic.

## Step 3: Architectural Refactoring (P3)
- [ ] TODO: Transition PyInstaller build from `--onefile` to `--onedir`.

## Verification Tasks
- [x] 8b1a95c Perform a full end-to-end upgrade from a previous version to the current one via the Tray Icon.
- [x] 8b1a95c Verify that the application restarts without "DLL not found" errors.
- [x] 8b1a95c Verify that the application is not running as Administrator after the update.
- [x] 8b1a95c Inspect the installer log (`%TEMP%\Setup Log...`) to confirm `OpenProcess` behavior.

## Phase: Review Fixes
- [x] 04cca29 Task: Apply review suggestions
