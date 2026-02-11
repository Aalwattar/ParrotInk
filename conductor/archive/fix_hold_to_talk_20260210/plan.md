# Implementation Plan: Fix 'Hold to Talk' Interruption Bug

## Phase 1: Logic & TDD [checkpoint: 67dbd7a]
Update the interaction monitor to respect the `hold_to_talk` setting.

- [x] Task: Create a reproduction test in `tests/test_interaction.py`.
    - [x] Simulate `hold_to_talk = true`.
    - [x] Mock a hotkey press (session start).
    - [x] Simulate another key press and verify the session *does not* stop.
    - [x] Mock hotkey release and verify the session *does* stop.
- [x] Task: Modify `engine/interaction.py` to disable "Stop on Any Key" when in hold mode.
    - [x] In the keyboard listener callback, add a check for `config.hold_to_talk`.
    - [x] If true, return immediately for any key that isn't the session-ending hotkey.
- [x] Task: Verify with `pytest`.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Logic & TDD' (Protocol in workflow.md)

## Phase 2: Final Validation [checkpoint: a6b407d]
Verify the fix in a real-world scenario.

- [x] Task: Manual Acceptance Test.
    - [x] Run the app with `hold_to_talk = true`.
    - [x] Verify that typing while holding the hotkey does not stop the transcription.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Final Validation' (Protocol in workflow.md)
