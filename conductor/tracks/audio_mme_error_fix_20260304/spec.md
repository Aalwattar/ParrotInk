# Specification: PortAudio/MME "Undefined external error" Fix

## Goal
Resolve the `PaErrorCode -9999` error preventing audio capture and session starts.

## Problem Statement
- Users report `[ERROR] [Audio] Stereo capture fallback also failed: Error opening InputStream: Unanticipated host error [PaErrorCode -9999]: 'Undefined external error.' [MME error 1]`.
- This often happens when another app (like Chrome/Discord) has exclusive control of the device, or when the sample rate/buffer size requested by PyAudio is rejected by the MME driver.
- The failure to open the audio stream results in an "Error starting session" message.

## Proposed Changes
1.  **Audio Stream Robustness**:
    -   Improve the error handling in `engine/services/audio/` during stream initialization.
    -   Try falling back to different sample rates (e.g., 44100 -> 16000) or mono capture if stereo fails.
    -   Verify the sample rate support before attempting to open the stream.
2.  **Diagnostic Feedback**:
    -   If a hardware error occurs, provide a clearer message in the HUD: "Audio device unavailable. Please check if another app is using the microphone."
3.  **Config Validation**:
    -   Ensure AssemblyAI/Provider configurations aren't forcing incompatible audio formats.

## Success Criteria
- Graceful failure or successful fallback when MME/DirectSound device is "busy".
- Detailed logging for `PaErrorCode -9999` to identify the root cause (sample rate, bit depth, or exclusive mode).
- HUD provides actionable advice for hardware errors.
