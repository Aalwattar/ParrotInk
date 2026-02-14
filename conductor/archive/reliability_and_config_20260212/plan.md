# Implementation Plan: Reliability & Configuration

Apply improvements to session management, configuration exposure, and hardware compatibility.

## Phase 1: Session Rotation (I3)
Goal: Perform rotation during idle time.

- [x] Task: Update `ConnectionManager.ensure_connected` logic to support "lazy rotation" vs "immediate rotation".
- [x] Task: Call `ensure_connected` (or a specific rotation check) inside `ConnectionManager.start_idle_timer`.
- [x] Task: Verify rotation occurs immediately after `stop_listening` if the session is old.
- [x] Task: Conductor - User Manual Verification 'Immediate Rotation'

## Phase 2: Configuration & Hardware (I4, I7)
Goal: Expose knobs and support stereo devices.

- [x] Task: Update `OpenAIProvider._update_session` to use all fields from `config.providers.openai.advanced`.
- [x] Task: Refactor `AudioStreamer.start` to attempt a 2-channel fallback if 1-channel `sd.InputStream` creation fails.
- [x] Task: Investigate `winsound` volume limitation. If impossible without heavy libs, explicitly log that volume is ignored for now or switch to a lightweight alternative (e.g., `sounddevice` playback).
- [x] Task: Conductor - User Manual Verification 'Hardware & Config'

## Phase 3: Final Verification
Goal: Ensure zero regressions.

- [x] Task: Run full test suite.
- [x] Task: Pass DOD Gate.
- [x] Task: Conductor - User Manual Verification 'Reliability Finalization'
