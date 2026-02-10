# Implementation Plan: Smart Interaction & Polish

## Phase 1: Modular Interaction Monitor
Extract and isolate the interaction logic.

- [x] Task: Create `engine/interaction.py` to handle trigger detection
    - [x] Task: Write tests for an `InteractionMonitor` class that can register keyboard callbacks.
    - [x] Task: Implement the base class and a `KeyboardTrigger` using `pynput.keyboard.Listener`.
- [x] Task: Implement "Any Key" Stop Logic
    - [x] Task: Write tests verifying that *any* key press (not just the hotkey) triggers the "Stop" event.
    - [x] Task: Configure the listener to fire a stop signal on `on_press` for any key.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Modular Interaction Monitor' (Protocol in workflow.md)

## Phase 2: Integration & Injection Suppression
Connect the new monitor to the `AppCoordinator` and handle the manual priority.

- [x] Task: Update `AppCoordinator` to use `InteractionMonitor`
    - [x] Task: Write tests for `AppCoordinator` ensuring it subscribes to the monitor's signals.
    - [x] Task: Refactor `main.py` to delegate hotkey and "any key" detection to the new module.
- [x] Task: Implement "Discard on Manual" Logic
    - [x] Task: Write a test where a transcription arrives *after* a manual key press has stopped the session, and verify `inject_text` is NOT called.
    - [x] Task: Add a `session_cancelled` flag to the coordinator that is set when a manual key terminates the listening state.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Integration & Injection Suppression' (Protocol in workflow.md)

## Phase 3: Polish & Cleanup
Ensure the UI and logs reflect the new behavior correctly.

- [x] Task: Final Smoke Tests and State Verification
    - [x] Task: Write integration tests for the full flow: Start -> Type Key -> Verify Idle state & No Injection.
    - [x] Task: Ensure tray icon transitions remain smooth and accurate.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Polish & Cleanup' (Protocol in workflow.md)
