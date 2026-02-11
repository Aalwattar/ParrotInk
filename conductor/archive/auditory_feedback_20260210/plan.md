# Implementation Plan: Auditory Feedback for Recording State

## Phase 1: Configuration & Sound Engine
Implement the configuration models and a lightweight utility for audio playback.

- [x] Task: Update `engine/config.py` with the `interaction.sounds` schema.
    - [x] Create `SoundsConfig` Pydantic model.
    - [x] Add `sounds` field to `Config` (via `InteractionConfig` if created, or directly).
- [x] Task: Update `config.example.toml` with the new sound settings.
- [x] Task: Create `engine/audio_feedback.py` for sound playback.
    - [x] Use `winsound` (built-in Windows) or a lightweight library for low-latency WAV playback.
    - [x] Implement `play_sound(path, volume)` with error handling for missing files.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Configuration & Sound Engine' (Protocol in workflow.md)

## Phase 2: Assets & Lifecycle Integration
Prepare the audio assets and integrate them into the dictation start/stop flow.

- [x] Task: Create `assets/sounds/` directory and add placeholder `.wav` files.
    - [x] Use subtle, short sounds for "start" (click) and "stop" (soft closing).
- [x] Task: Integrate "Start" sound into `AppCoordinator.start_listening`.
    - [x] Play sound *after* `await self.provider.start()` succeeds.
- [x] Task: Integrate "Stop" sound into `AppCoordinator.stop_listening`.
    - [x] Play sound *after* `await self.provider.stop()` and `streamer.stop()`.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Assets & Lifecycle Integration' (Protocol in workflow.md)

## Phase 3: UI Integration
Add the configuration toggle to the system tray menu.

- [x] Task: Update `engine/ui.py` to support a "Settings" sub-menu.
    - [x] Add `Settings` MenuItem with a sub-menu.
    - [x] Add "Enable Audio Feedback" checkbox/toggle in the sub-menu.
- [x] Task: Connect UI toggle to `AppCoordinator` and configuration state.
- [x] Task: Conductor - User Manual Verification 'Phase 3: UI Integration' (Protocol in workflow.md)

## Phase 4: Final Validation
Verify the blocking start behavior and UX quality.

- [x] Task: Verify TDD coverage for the sound engine and config resolution.
- [x] Task: Perform manual smoke tests for "No Lost Words" (blocking start).
- [x] Task: Conductor - User Manual Verification 'Phase 4: Final Validation' (Protocol in workflow.md)
