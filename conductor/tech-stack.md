# Technology Stack

## 1. Programming Language

- **Python:** The primary language for the application, chosen for its extensive libraries for audio processing, web connectivity, and system integration.

## 2. Core Libraries

- **sounddevice:** Used for capturing real-time audio from the microphone.
- **websockets:** Enables low-latency, real-time streaming of audio data to the transcription APIs.
- **httpx:** Used for making standard HTTP requests to API endpoints where streaming is not required.
- **pywin32:** Provides robust, low-level access to the Windows API for creating global hotkeys and injecting text at the cursor location.
- **pystray:** Manages the application's system tray icon and context menu.

## 3. API SDKs

- **openai:** The official Python client for interacting with OpenAI's transcription services.
- **assemblyai:** The official Python client for interacting with AssemblyAI's transcription services.

## 4. Alternatives

- **pynput:** Can be used as a simpler, higher-level alternative to `pywin32` for managing global hotkeys if `pywin32` proves too complex for the initial implementation.
