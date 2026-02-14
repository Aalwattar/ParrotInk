# Technology Stack

## 1. Programming Language

- **Python:** The primary language for the application, chosen for its extensive libraries for audio processing, web connectivity, and system integration.

## 2. Core Libraries

- **sounddevice:** Used for capturing real-time audio from the microphone.
- **numpy:** Used for processing and transforming audio chunks (e.g., float32 to int16 conversion) before transmission.
- **websockets:** Enables low-latency, real-time streaming of audio data to the transcription APIs.
- **httpx:** Used for making standard HTTP requests to API endpoints where streaming is not required.
- **pywin32:** Provides robust, low-level access to the Windows API for creating global hotkeys and injecting text at the cursor location.
- **pystray:** Manages the application's system tray icon and context menu.
- **threading:** Used to run the UI loop in a background thread, ensuring the main thread remains responsive to system signals.
- **pydantic:** Used for robust configuration management, validation, and schema definition.
- **pydantic-settings:** Extends pydantic for environment-based configuration and settings management.
- **platformdirs:** Resolves platform-specific user directories for log files and configuration.
- **keyring:** Accesses the system's keyring service (Windows Credential Manager) for secure secret storage.
- **pynput:** Powering the `InteractionMonitor` and `HotkeyRecorder`, used to detect global keyboard events and record user-defined shortcuts.
- **signal:** Implements immediate, double-confirmation Ctrl+C shutdown logic for improved CLI responsiveness.
- **Pillow (PIL):** Used for dynamic, procedural generation of high-DPI tray icons at runtime.
- **skia-python:** Powers the high-performance, hardware-accelerated HUD rendering with anti-aliased typography.
- **tomllib:** (Standard Library) Used for safe parsing of `pyproject.toml` to extract application metadata.
- **tomli-w:** Used for writing configuration files in TOML format.
- **pyinstaller:** (Build Tool) Used to package the Python application into a standalone Windows executable.

## 3. API SDKs

- **openai:** The official Python client for interacting with OpenAI's transcription services.
- **assemblyai:** The official Python client for interacting with AssemblyAI's transcription services.

## 4. Alternatives

- **pynput:** Can be used as a simpler, higher-level alternative to `pywin32` for managing global hotkeys if `pywin32` proves too complex for the initial implementation.
