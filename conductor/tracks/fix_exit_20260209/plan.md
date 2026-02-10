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

- [x] Task: Resolve `SystemExit` Traceback in `engine/ui.py` (f889dd6)
    - [x] **Red:** Create a reproduction case (script) that triggers the `SystemExit` traceback during shutdown.
    - [x] **Green:** Ensure `app.stop()` is called from the main thread and correctly triggers `icon.stop()`.
    - [x] **Green:** Remove any direct `sys.exit()` calls within handlers that might be executed in the `pystray` loop context.
- [x] Task: Implement Bounded Shutdown (<= 2s) (697fe8a)
    - [x] **Green:** Update shutdown sequence to wait for the UI thread with a 2-second timeout.
    - [x] **Green:** Ensure all background threads (audio, etc.) are marked as `daemon=True`.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Clean Shutdown and Traceback Fix' (Protocol in workflow.md)

## Phase 3: Tray Menu Exit Fix
Ensure that choosing 'Quit' from the tray menu correctly signals the main thread to exit.

- [x] Task: Fix Tray Menu Exit Hang (c9dc7b6)
    - [x] **Red:** Create a reproduction script showing the main thread hanging after `app.stop()` is called from the UI.
    - [x] **Green:** Implement a shared `shutdown_event` between `main.py`, `ShutdownHandler`, and `TrayApp`.
    - [x] **Refactor:** Centralize shutdown logic to avoid redundant termination sequences.
