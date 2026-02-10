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
    - Hotkey assignment and "hold_mode" boolean.
    - Transcription language.
    - **Advanced Configuration:** Custom API endpoints (URLs) for transcription providers to support local mock servers or proxies.
    - Custom word overrides or vocabulary lists to improve accuracy.
    - Simple post-processing rules for the transcribed text.

## 3. Technical Specifications

### 3.1. Audio Pipeline
- **Audio Capture:** Use `sounddevice` for microphone input.
- **Encoding & Streaming:**
    - **OpenAI:** Audio must be resampled to 24kHz mono PCM and streamed.
    - **AssemblyAI:** Audio must be streamed over a secure WebSocket (WSS) connection, with a default sample rate of 16kHz.
- **Real-time Transport:** Use the `websockets` library for low-latency streaming. The application must gracefully handle connection errors and reconnect attempts.

### 3.2. Windows Integration
- **Hotkeys:** The preferred implementation is the `pywin32` library to register global system hotkeys for robustness. `pynput` is a viable alternative.
- **Text Injection:** Use `pywin32` to simulate `SendInput` events for seamless text injection. A fallback mechanism using the clipboard (preserving its original content) should be available.

### 3.3. Dependencies
- **Audio:** `sounddevice==0.5.5`
- **Networking:** `websockets==16.0`, `httpx==0.28.1`
- **API SDKs:** `openai==2.17.0`, `assemblyai==0.50.0`
- **Windows Integration:** `pywin32==311`, `pystray==0.19.5`
- **Hotkey Alternative:** `pynput==1.8.1`
