# Implementation Plan: Audio Device Selection & Ducking Mitigation

## Phase 1: Configuration to Streamer Bridge
- [x] Task: Update `AppCoordinator.__init__` in `main.py` to fetch `input_device` from config.
- [x] Task: Update `AppCoordinator.start` or session start logic to ensure `input_device` is passed to the streamer.
- [x] Task: Handle "default" or empty string cases to maintain current fallback behavior.

## Phase 2: Streamer Device Targeting
- [x] Task: Modify `AudioStreamer.__init__` in `engine/audio/streamer.py` to accept an optional `device_name` or `device_index`.
- [x] Task: Update `AudioStreamer._try_open_stream` to find the correct device index if a name is provided.
- [x] Task: Pass the `device` parameter to `sd.InputStream`.

## Phase 3: Ducking & Unresponsiveness Mitigation
- [x] Task: Investigate and apply `sd.WasapiSettings(role=sd.WASAPI.Role.Multimedia)` to mitigate ducking. (Applied WASAPI Shared Mode with auto-convert as the most compatible mitigation)
- [x] Task: Ensure thread isolation for stream opening to prevent hotkey lag.

## Phase: Review Fixes
- [x] Task: Fix PaErrorCode -9984 by guarding WASAPI settings.
- [x] Task: Enhance device selection to prioritize WASAPI host API.
- [x] Task: Add robustness guards for device and host API indices.
