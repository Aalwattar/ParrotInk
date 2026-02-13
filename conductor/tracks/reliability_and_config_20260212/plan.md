# Implementation Plan: Reliability & Configuration

Apply improvements to session management, configuration exposure, and hardware compatibility.

## Phase 1: Session Rotation (I3)
Goal: Perform rotation during idle time.

- [ ] Task: Update `ConnectionManager.ensure_connected` logic to support "lazy rotation" vs "immediate rotation".
- [ ] Task: Call `ensure_connected` (or a specific rotation check) inside `ConnectionManager.start_idle_timer`.
- [ ] Task: Verify rotation occurs immediately after `stop_listening` if the session is old.
- [ ] Task: Conductor - User Manual Verification 'Immediate Rotation'

## Phase 2: Configuration & Hardware (I4, I7)
Goal: Expose knobs and support stereo devices.

- [ ] Task: Update `OpenAIProvider._update_session` to use all fields from `config.providers.openai.advanced`.
- [ ] Task: Refactor `AudioStreamer.start` to attempt a 2-channel fallback if 1-channel `sd.InputStream` creation fails.
- [ ] Task: Investigate `winsound` volume limitation. If impossible without heavy libs, explicitly log that volume is ignored for now or switch to a lightweight alternative (e.g., `sounddevice` playback).
- [ ] Task: Conductor - User Manual Verification 'Hardware & Config'

## Phase 3: Final Verification
Goal: Ensure zero regressions.

- [ ] Task: Run full test suite.
- [ ] Task: Pass DOD Gate.
- [ ] Task: Conductor - User Manual Verification 'Reliability Finalization'
