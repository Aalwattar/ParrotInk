# Implementation Plan: Standalone EXE Build (DevOps)

## Phase 1: Foundation & Path Resolution [checkpoint: 35d78d9]
- [x] Task: Implement Windows path helpers in `engine/platform_win/paths.py` (c4843e4)
    - [x] Create `get_app_dir()`, `get_config_path()`, and `get_log_path()` helpers.
    - [x] Ensure they resolve to `%APPDATA%\ParrotInk`.
- [x] Task: Update `engine/config.py` to use path helpers for default config location. (2f541b0)
- [x] Task: Update logging initialization in `engine/logging.py` to use path helpers for default log file location. (f38c09e)
- [x] Task: Conductor - User Manual Verification 'Phase 1: Foundation & Path Resolution' (Protocol in workflow.md)

## Phase 2: Build Configuration & Dependencies [checkpoint: ee58106]
- [x] Task: Add `pyinstaller` to development dependencies. (1a29dd8)
    - [x] Run `uv add --dev pyinstaller`.
- [x] Task: Create PyInstaller spec file at `build/pyinstaller/parrotink_onefile.spec`. (df11ec6)
    - [x] Configure `onefile` and `noconsole` modes.
    - [x] Include hidden imports for `pynput`, `pystray`, `PIL`, `websockets`, `keyring`.
    - [x] Include binaries for `sounddevice` (PortAudio).
    - [x] Include `assets/` directory.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Build Configuration & Dependencies' (Protocol in workflow.md)

## Phase 3: Build Scripts & Distribution [checkpoint: 83274eb]
- [x] Task: Create manual build script `scripts/build_onefile.ps1`. (f6389f2)
    - [x] Implement cleaning of `build/` and `dist/` directories.
    - [x] Implement `uv sync --dev` for dependency management.
    - [x] Execute PyInstaller using the defined spec file.
    - [x] Added `scripts/clean_build.ps1` for general cleanup.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Build Scripts & Distribution' (Protocol in workflow.md)

## Phase 4: Final Verification [checkpoint: 5e426f9]
- [x] Execute build script and verify artifact generation. (83274eb)
- [x] Perform manual smoke test of the generated `dist/ParrotInk.exe`.
    - [x] Verify tray icon, hotkeys, and transcription functionality.
    - [x] Verify config and log placement in `%APPDATA%\ParrotInk`.
- [x] Task: Conductor - User Manual Verification 'Phase 4: Final Verification' (Protocol in workflow.md)
