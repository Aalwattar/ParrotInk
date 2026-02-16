# Specification: Standalone EXE Build (DevOps)

## Overview
Implement a manual build process to produce a standalone, single-file Windows executable (`ParrotInk.exe`) for the application. This includes fixing runtime path resolution for packaged execution and creating a reproducible PyInstaller configuration.

## Functional Requirements
- **Path Management:** Implement `engine/platform_win/paths.py` to resolve application data paths (config, logs) to `%APPDATA%\ParrotInk`.
- **Runtime Path Integration:** Update configuration loading and logging initialization to use the new path helpers when running in a packaged environment.
- **Build Configuration:** Create `build/pyinstaller/parrotink_onefile.spec` with necessary hidden imports and binary collections:
    - Hidden Imports: `pynput`, `pystray`, `PIL`, `websockets`, `keyring`, `keyring.backends.Windows`.
    - Binaries: `sounddevice` (PortAudio DLLs).
    - Entrypoint: `main.py`.
- **Build Script:** Create `scripts/build_onefile.ps1` that performs:
    1. Workspace cleaning (`build/`, `dist/`).
    2. Dependency sync via `uv sync --dev`.
    3. PyInstaller execution using the spec file.

## Non-Functional Requirements
- **Platform:** Windows target only.
- **Packaging:** `--onefile` and `--noconsole` (GUI mode).
- **Manual Trigger:** Build is initiated manually via PowerShell script.

## Acceptance Criteria
- Running `scripts/build_onefile.ps1` produces `dist/ParrotInk.exe`.
- The EXE launches successfully without a console window.
- The system tray icon appears and is functional.
- Hotkeys and transcription providers work correctly.
- Configuration is saved to and loaded from `%APPDATA%\ParrotInk\config.toml`.
- Logs are written to `%APPDATA%\ParrotInk\parrotink.log`.

## Out of Scope
- Automated CI/CD (GitHub Actions) integration.
- Multi-platform support (macOS/Linux).
- `onedir` distribution mode.
