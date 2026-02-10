# Implementation Plan: Fix pystray SystemExit and Double Ctrl+C Responsiveness

## Phase 1: Threading and Signal Logic Refactor [checkpoint: 8d4ecc9]
Refactor the application entry point to separate the UI loop from the signal-handling main thread.

- [x] Task: Refactor `main.py` for Threaded UI and Signal Responsiveness (f889dd6)
    - [x] **Red:** Write a test utility or script to verify that `SIGINT` is caught immediately while a dummy `pystray` icon is "running".
    - [x] **Green:** Update `main.py` to move `app.run()` to a background thread.
    - [x] **Green:** Implement the main thread loop waiting on a `threading.Event`.
    - [x] **Refactor:** Ensure `sys.stdout.flush()` is used for all signal-related prints.
- [x] Task: Implement Double Ctrl+C Confirmation Logic (f889dd6)
    - [x] **Red:** Write unit tests for a `SignalHandler` class that manages the 3-second window and state transitions.
    - [x] **Green:** Implement `SignalHandler` with timestamp-based logic for double-press detection.
    - [x] **Refactor:** Clean up global variables by encapsulating signal state in a class or closure.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Threading and Signal Logic Refactor' (Protocol in workflow.md)

## Phase 2: Clean Shutdown and Traceback Fix
Ensure the transition from signal confirmation to `pystray` termination is silent and fast.

- [ ] Task: Resolve `SystemExit` Traceback in `engine/ui.py`
    - [ ] **Red:** Create a reproduction case (script) that triggers the `SystemExit` traceback during shutdown.
    - [ ] **Green:** Ensure `app.stop()` is called from the main thread and correctly triggers `icon.stop()`.
    - [ ] **Green:** Remove any direct `sys.exit()` calls within handlers that might be executed in the `pystray` loop context.
- [ ] Task: Implement Bounded Shutdown (<= 2s)
    - [ ] **Green:** Update shutdown sequence to wait for the UI thread with a 2-second timeout.
    - [ ] **Green:** Ensure all background threads (audio, etc.) are marked as `daemon=True`.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Clean Shutdown and Traceback Fix' (Protocol in workflow.md)
