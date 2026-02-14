# Product Definition

## 1. Initial Concept

The user wants to build a real-time voice-to-text application for Windows. It should use online transcription APIs (OpenAI and AssemblyAI) and inject the resulting text at the user's current cursor position. The application should be configurable and run as a system tray utility.

## 2. Core Features

### 2.1. Real-time Transcription
- The application will capture audio from the user's microphone and stream it to a selected online transcription service in real-time.
- It must handle and display both partial (interim) and final transcription results.

### 2.2. API Provider Support
- **OpenAI:** Integrate with OpenAI's real-time transcription service.
- **AssemblyAI:** Integrate with AssemblyAI's real-time transcription service.
- The user can select the desired provider through the application's settings.

### 2.3 Hotkey Control
- **Unified Hotkey:** The application uses a single configurable hotkey for control.
- **Smart Interaction:** The hotkey serves as the "Start" trigger. Once active, **any** keyboard interaction (including the hotkey itself or modifiers) acts as a "Stop" command.
- **Manual Priority:** To prevent AI interference with manual typing, if a session is stopped by a key press, any pending transcription text is discarded. The user's manual input always takes precedence.

### 2.4 Text Injection
- The primary function is to inject the final transcribed text directly at the current text cursor's location in the active application.
- The injection should simulate keyboard typing to ensure broad compatibility.

### 2.5. System Tray Application
- The application will run as a background process with an icon in the system tray.
- The tray icon will provide visual feedback on the application's status (e.g., idle, listening, error).
- A context menu on the tray icon will allow the user to:
    - Enable or disable transcription.
    - Select the active transcription provider.
    - Open the settings/configuration file.
    - Exit the application.

### 2.6. Configuration
- All settings will be managed through a local configuration file in TOML format for easy editing.
- Configurable options will include:
    - API provider selection, API keys, and **Test Mode** toggle.
    - **Secure Credential Management:** API keys are stored securely in the Windows Credential Manager and never saved in plain text configuration files.
    - **Smart UI Validation:** Providers are automatically disabled (grayed out) in the system tray if their required credentials are missing, unless in Test Mode.
    - **User-Friendly Profiles:** High-level `latency_profile` (fast, balanced, accurate) and `mic_profile` (headset, laptop) simplify complex engineering parameters.
    - **Granular Advanced Settings:** Power users can still override profiles to fine-tune VAD thresholds, models, and silence durations.
    - **Configuration Fidelity:** All engine parameters, including session rotation, connection timeouts, and voice activity thresholds, are exposed and respected, ensuring the config file is the single source of truth.
    - **AssemblyAI V3 Integration:** Leverages the latest AssemblyAI Streaming V3 API for improved performance and more detailed session control.
    - **Verbose Debugging & Structured Logging:** Multi-level, non-blocking logging to console and file, with automatic redaction of secrets and truncation of audio data.
    - **Interactive Hotkey Setup:** Users can record their desired hotkey combination directly through a tray-driven recording dialog.
    - **Diagnostics:** A new `app config --explain` CLI command provides a clear report of how high-level profiles map to specific technical timings and thresholds.
    - Transcription language.
    - **Advanced Configuration:** Custom API endpoints (URLs) for transcription providers to support local mock servers or proxies.

### 2.8. Headless Evaluation Mode
- A dedicated CLI mode (`eval`) for deterministic accuracy testing and regression monitoring.
- Replays WAV files through the existing transcription pipeline without triggering UI, text injection, or audio feedback.
- Produces structured JSON output containing transcription results and performance metrics (latency, final text).

### 2.7. Tray Interaction
- **Provider Selection:** Users can switch between providers directly from the tray menu.
- **Visual Feedback:** The app indicates its state (Idle, Listening, Error) through the tray icon color.
- **Dynamic Menu:** The "Default Provider" setting from the config determines the initial selection, and availability is checked dynamically.
    - Custom word overrides or vocabulary lists to improve accuracy.
    - Simple post-processing rules for the transcribed text.

### 2.9. Distribution
- **Standalone Executable:** The application can be packaged as a single, portable Windows executable (`Voice2Text.exe`) for easy distribution and installation.
    - **Portable Paths:** When running as an EXE, the application correctly resolves configuration and log files to the user's `%APPDATA%\Voice2Text` directory, ensuring it works even when launched from read-only locations.
    - **Single Instance Protection:** The application uses a Win32 Mutex to ensure only one instance is running at a time, preventing hotkey and microphone conflicts. If a second instance is launched, it displays a helpful notification and exits gracefully.
    - **Automation-Friendly:** A `--background` CLI flag allows the application to start silently without the "already running" warning, ideal for startup scripts and automation.
## 3. Technical Specifications

### 3.1. Audio Pipeline
- **Audio Capture:** Use `sounddevice` for microphone input.
- **Encoding & Streaming:**
        - **OpenAI:** Audio must be resampled to 24kHz mono PCM and streamed.
        - **AssemblyAI:** Audio must be streamed over a secure WebSocket (WSS) using the **Streaming V3 API**, sending raw binary audio frames.
    - **Real-time Transport:** Use the `websockets` library for low-latency streaming.
     The application must gracefully handle connection errors and reconnect attempts.

### 3.2. Windows Integration
- **Hotkeys:** The preferred implementation is the `pywin32` library to register global system hotkeys for robustness. `pynput` is a viable alternative.
- **Text Injection:** Use `pywin32` to simulate `SendInput` events for seamless text injection. A fallback mechanism using the clipboard (preserving its original content) should be available.

### 3.3. Dependencies
- **Audio:** `sounddevice==0.5.5`
- **Networking:** `websockets==16.0`, `httpx==0.28.1`
- **API SDKs:** `openai==2.17.0`, `assemblyai==0.50.0`
- **Windows Integration:** `pywin32==311`, `pystray==0.19.5`
- **Hotkey Alternative:** `pynput==1.8.1`
