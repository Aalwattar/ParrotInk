# Track Specification: Headless Evaluation Mode (Eval)

## Overview
Add a test-only, headless CLI mode (`eval`) to `voice2text` that replays a WAV file through the existing transcription pipeline. This allows for deterministic accuracy testing and regression monitoring without requiring a UI or manual speech.

## 1. Functional Requirements

### 1.1 Command Interface
- **Command:** `python main.py eval`
- **Required Flags:**
    - `--audio <path.wav>`: Path to the input WAV file.
    - `--provider <openai|assemblyai>`: Selects the transcription provider.
- **Optional Flags:**
    - `--config <path.toml>`: Custom configuration file.
    - `--chunk-ms <int>`: Chunk duration (overrides config, default 100ms).
    - `--timeout-seconds <int>`: Maximum wait time for finalization (default 120s).

### 1.2 Execution Logic (Headless)
- **Import Isolation:** The `eval` execution path MUST NOT import `pystray`, `tkinter`, or any UI-related modules.
- **Microphone:** Hardware microphone capture must be disabled.
- **Injection:** Text injection to the active window must be disabled.
- **Feedback:** Auditory feedback (beeps/sounds) must be disabled.
- **Logging:** All non-JSON output (logs/errors) must go to `stderr`.

### 1.3 Audio Processing
- **Format:** Accept 16-bit PCM WAV only.
- **Normalization:** If the input is stereo or multi-channel, it must be downmixed to mono before being passed to the `AudioAdapter`.
- **Pacing:** Replay must be paced in real-time to simulate live dictation, using the specified `chunk-ms`.

## 2. Output Contract
On success, the tool must print exactly one JSON object to `stdout`:
```json
{
  "status": "ok",
  "provider": "openai|assemblyai",
  "audio_file": "path/to/file.wav",
  "config_file": "path/to/config.toml",
  "chunk_ms": 100,
  "realtime": true,
  "time_to_first_partial_s": 0.42,
  "time_to_first_final_s": 3.12,
  "final_text": "The transcribed text."
}
```

On failure, it must print:
```json
{
  "status": "error",
  "error_code": "invalid_wav|provider_auth|timeout|ws_error",
  "message": "Description of the error"
}
```

## 3. Acceptance Criteria
- [ ] `eval` produces a valid JSON transcript and exits with code 0.
- [ ] Running `eval` on a system without `tkinter` or `pystray` installed does not crash.
- [ ] Stereo WAV files are correctly downmixed to mono for the provider.
- [ ] No tray icon or UI windows appear during execution.

## 4. Out of Scope
- Non-WAV audio formats (MP3, FLAC, etc.).
- Non-realtime (faster than real-time) replay mode.
- Manual commit/SHA tagging in the JSON output.
