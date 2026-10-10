# Technology Stack

## 1. Programming Language

- **Python:** The primary language for the application, chosen for its extensive libraries for audio processing, web connectivity, and system integration.

## 2. Core Libraries

- **sounddevice:** Used for capturing real-time audio from the microphone. Now enhanced with **WASAPI Shared mode** support for robust platform integration and ducking mitigation on Windows.
- **numpy:** Used for processing and transforming audio chunks (e.g., float32 to int16 conversion) before transmission.
- **websockets:** Enables low-latency, real-time streaming of audio data to the transcription APIs.
- **httpx:** Used for making standard HTTP requests to API endpoints where streaming is not required.
- **pywin32:** Provides robust, low-level access to the Windows API for creating global hotkeys and injecting text at the cursor location.
- **pystray:** Manages the application's system tray icon and context menu.
- **ttkbootstrap:** Provides themed UI components using the shared `bootstrap-dark` theme for application windows and dialogs.
- **threading:** Used to run the UI loop in a background thread, ensuring the main thread remains responsive to system signals.
- **pydantic:** Used for robust configuration management, validation, and schema definition.
- **pydantic-settings:** Extends pydantic for environment-based configuration and settings management.
- **platformdirs:** Resolves platform-specific user directories for log files and configuration.
- **keyring:** Accesses the system's keyring service (Windows Credential Manager) for secure secret storage.
- **Native Win32 input (`ctypes`):** A dedicated `WH_KEYBOARD_LL` thread detects and suppresses hotkeys. The recorder handles native window messages, and the mouse monitor polls Windows state. No `keyboard` or `pynput` library is used.
- **soxr (python-soxr):** High-quality, stateful audio resampling library used to convert microphone capture rates to provider-specific requirements (e.g., 24kHz for OpenAI).
- **skia-python:** Powers the high-performance, hardware-accelerated HUD rendering with anti-aliased typography.
- **tomllib:** (Standard Library) Used for safe parsing of `pyproject.toml` to extract application metadata.
- **tomlkit:** Used for style-preserving TOML management to maintain user comments and formatting when saving configuration programmatically.
- **pyinstaller:** (Build Tool) Used to package the Python application into a standalone Windows executable.
- **Inno Setup (ISCC):** (Build Tool) Used to create a professional Windows installer (`ParrotInk-Setup.exe`) that manages installation, uninstallation, and process-aware updates.
- **Deterministic Process Handoff:** (Pattern) Implementation of a robust upgrade cycle using `ctypes.windll.kernel32.SetDllDirectoryW(None)` to reset the DLL search path and `ctypes.windll.shell32.ShellExecuteW` for detached, UAC-aware installer launching. This prevents inherited environment poisoning from frozen PyInstaller processes.
- **Windows BITS (Background Intelligent Transfer Service):** (Integrated OS Service) Leveraged via PowerShell to perform robust, low-impact, and persistent background downloads of application updates.
- **win11toast:** Provides a simple, Pythonic interface for displaying native Windows 10/11 toast notifications upon application startup.
- **packaging:** Used for robust Semantic Versioning (SemVer) comparison between local and remote application versions.
- **webbrowser:** (Standard Library) Used to securely open the GitHub releases page in the user's default browser.

## 3. Validation SDKs

- **openai** and **assemblyai:** Used by standalone golden-transcription and connectivity-validation tools. The live application connects to both providers through `websockets` directly, so these SDKs are development dependencies rather than runtime dependencies.

## 4. Alternatives

- **Input libraries:** The earlier `keyboard` and `pynput` implementations were replaced by native Windows hooks to address stale hooks, stuck modifiers, and shutdown failures. Keep the native implementation.

## 5. CI/CD & Automation
- **GitHub Actions:** Provides automated CI/CD pipelines for linting, testing, and building the application.
    - **astral-sh/setup-uv@v7:** Used to set up the `uv` environment with caching for fast and reproducible builds.
    - **softprops/action-gh-release@v2:** Automates the creation of GitHub Releases and asset uploading.
