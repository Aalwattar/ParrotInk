# Implementation Plan: Standalone EXE Build (DevOps)

## Phase 1: Foundation & Path Resolution
- [ ] Task: Implement Windows path helpers in `engine/platform_win/paths.py`
    - [ ] Create `get_app_dir()`, `get_config_path()`, and `get_log_path()` helpers.
    - [ ] Ensure they resolve to `%APPDATA%\Voice2Text`.
- [ ] Task: Update `engine/config.py` to use path helpers for default config location.
- [ ] Task: Update logging initialization in `engine/logging.py` to use path helpers for default log file location.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Foundation & Path Resolution' (Protocol in workflow.md)

## Phase 2: Build Configuration & Dependencies
- [ ] Task: Add `pyinstaller` to development dependencies.
    - [ ] Run `uv add --dev pyinstaller`.
- [ ] Task: Create PyInstaller spec file at `build/pyinstaller/voice2text_onefile.spec`.
    - [ ] Configure `onefile` and `noconsole` modes.
    - [ ] Include hidden imports for `pynput`, `pystray`, `PIL`, `websockets`, `keyring`.
    - [ ] Include binaries for `sounddevice` (PortAudio).
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Build Configuration & Dependencies' (Protocol in workflow.md)

## Phase 3: Build Scripts & Distribution
- [ ] Task: Create manual build script `scripts/build_onefile.ps1`.
    - [ ] Implement cleaning of `build/` and `dist/` directories.
    - [ ] Implement `uv sync --dev` for dependency management.
    - [ ] Execute PyInstaller using the defined spec file.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Build Scripts & Distribution' (Protocol in workflow.md)

## Phase 4: Final Verification
- [ ] Task: Execute build script and verify artifact generation.
- [ ] Task: Perform manual smoke test of the generated `dist/Voice2Text.exe`.
    - [ ] Verify tray icon, hotkeys, and transcription functionality.
    - [ ] Verify config and log placement in `%APPDATA%\Voice2Text`.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Final Verification' (Protocol in workflow.md)
