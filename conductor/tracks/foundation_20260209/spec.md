# Track Specification: Foundation & Core Engine

## 1. Overview
This track focuses on building the core infrastructure of the `voice2text` application. This includes the background process (system tray), the configuration management system, the audio capture pipeline, and the real-time transcription connectors for OpenAI and AssemblyAI.

## 2. Technical Requirements

### 2.1 Configuration Management
- **Format:** TOML (using Python's built-in `tomllib` or `tomli` fallback).
- **Location:** `config.toml` in the application root.
- **Fields:**
  - `active_provider`: "openai" or "assemblyai".
  - `openai_api_key`: string.
  - `assemblyai_api_key`: string.
  - `hotkeys`:
    - `hold_to_talk`: string (e.g., "ctrl+alt+v").
    - `toggle_listen`: string.
  - `transcription`:
    - `language`: string (default "en").
    - `sample_rate`: integer (default 16000).

### 2.2 System Tray UI (`pystray`)
- **Icon:** Represent application state (Idle, Listening, Error).
- **Menu:**
  - Status indicator (Read-only).
  - Provider selection (Radio items).
  - Open Config (System command to open `config.toml`).
  - Exit.

### 2.3 Audio Capture (`sounddevice`)
- Capture mono audio stream from the default input device.
- Use a callback-based or generator-based approach to yield audio chunks.
- Handle buffering for real-time streaming.

### 2.4 Transcription Engine
- **OpenAI Integration:**
  - Stream audio to OpenAI real-time transcription endpoint.
  - Handle interim and final transcripts.
- **AssemblyAI Integration:**
  - Stream audio via WebSocket.
  - Handle interim and final transcripts.

### 2.5 Text Injection (`pywin32`)
- Provide a utility to inject text at the current cursor position using `SendInput`.

## 3. Architecture
- `main.py`: Entry point, initializes the tray app.
- `engine/`:
  - `config.py`: Configuration loader and validator.
  - `audio.py`: Audio capture and processing.
  - `injector.py`: Windows text injection utilities.
  - `transcription/`:
    - `base.py`: Abstract base class for providers.
    - `openai_provider.py`: OpenAI implementation.
    - `assembly_provider.py`: AssemblyAI implementation.

## 4. Acceptance Criteria
- App starts in the system tray.
- Tray icon changes when "Listening" state is triggered (mocked or real).
- Configuration is loaded from `config.toml`.
- Audio can be captured and yielded in chunks.
- (Draft) Transcription results are printed to console (before injection logic is finalized).
