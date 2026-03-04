# Implementation Plan: PortAudio/MME "Undefined external error" Fix

## Strategy
1.  Investigate `PaErrorCode -9999` behavior.
2.  Add a diagnostic helper to `engine/audio/streamer.py` to check for "busy" audio devices or unsupported sample rates.
3.  Add retry logic with different sample rates (16000, 44100, 48000) if initialization fails.
4.  If it still fails, show a descriptive message in the HUD: "Audio Hardware Busy. Close other apps using the microphone."

## Proposed Changes

### 1. `engine/audio/streamer.py`
-   Refine `AudioStreamer.start()`:
    -   Catch `Exception` during `sd.InputStream` creation.
    -   Log detailed `PaErrorCode` if available.
    -   Implement a fallback loop that tries 16000Hz (default) -> 44100Hz -> 48000Hz.
    -   If all fail, raise a specific `AudioHardwareError`.

### 2. `main.py`
-   In `start_listening`, catch `AudioHardwareError`.
-   Call `self.ui_bridge.show_error_message("Audio Hardware Busy\nPlease check your microphone settings.")`.

### 3. `engine/ui_bridge.py` & `engine/hud_renderer.py`
-   Add `show_error_message(msg)` to `UIBridge`.
-   Implement it in `HUDRenderer` to show the error message in Red (#EF4444).

## Verification Plan
1.  **Manual Test**: Run another app (like Chrome) with exclusive mic access (if possible to simulate). Press hotkey.
    -   Expect: HUD shows "Audio Hardware Busy" instead of log loop.
2.  **Mock Test**: Create a script that mocks `sd.InputStream` to throw `PaErrorCode -9999` and verify fallback logic.

## Phase: Review Fixes
- [x] Task: Apply review suggestions 21b946f
