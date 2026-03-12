# Audio Device Selection & Ducking Mitigation

## Objective
Address the "Sticky" audio device issue by ensuring the `AudioStreamer` respects user-configured device selections, while maintaining a robust "default" fallback. Mitigate Windows "Communication Ducking" and hotkey unresponsiveness caused by default audio routing conflicts.

## Context
Currently, the `AudioStreamer` hardcodes the audio capture to the system's default recording device, ignoring the `input_device` in the `.toml` configuration. When the app requests the default microphone upon hotkey press, Windows often categorizes this as "Communication" activity, which triggers global volume reduction (ducking) and can cause driver locks (making the hotkey feel unresponsive).

## Execution Plan

### Phase 1: Configuration to Streamer Bridge
- **Action:** Update the `AppCoordinator` (or equivalent orchestrator) to pass the configured `input_device` down to the `AudioStreamer` upon initialization and session start.
- **Action:** Retain the current fallback behavior: If `input_device` is "default", empty, or fails to open, fall back to the system default gracefully.

### Phase 2: Streamer Device Targeting
- **Action:** Modify `AudioStreamer._try_open_stream()` in `engine/audio/streamer.py` to accept and use the `device` parameter in `sd.InputStream()`.
- **Action:** Ensure that if a specific device ID/name is requested, the stream attempts to bind directly to that hardware, bypassing Windows' generic routing where possible.

### Phase 3: Ducking & Unresponsiveness Mitigation
- **Action:** Investigate the `sounddevice` / PortAudio WASAPI parameters to see if we can flag the stream as "Non-Communication" (e.g., `role=sd.WASAPI.Role.Multimedia`) to prevent Windows from ducking other audio.
- **Action:** If the ducking is unpreventable at the PortAudio level, document the Windows Sound Control Panel workaround for the user.
- **Action:** Ensure the stream opening process is strictly isolated from the hotkey listener thread to prevent driver locks from causing "multiple press" symptoms.

### Phase 4: Verification
- **Action:** Write/update tests to ensure `AudioStreamer` respects specific device IDs.
- **Action:** Manually verify that changing the device in the config and starting a new session utilizes the correct hardware.
