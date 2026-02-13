# Implementation Plan: Debug Silent Failure

Instrument and fix the connection hang.

## Phase 1: Instrumentation
Goal: Visualize the hang.

- [ ] Task: Add `print(..., flush=True)` to `main.py` -> `start_listening`.
- [ ] Task: Add `print(..., flush=True)` to `engine/connection.py` -> `ensure_connected`.
- [ ] Task: Add `print(..., flush=True)` to `engine/anchor.py` -> `capture_current`.
- [ ] Task: Conductor - User Manual Verification 'Check Prints'

## Phase 2: Fix & Cleanup
Goal: Resolve the issue based on findings (likely removing the blocking call).

- [ ] Task: If Anchor hangs: Disable anchor or fix ctypes usage.
- [ ] Task: If Connection hangs: Check `websockets` or network timeout.
- [ ] Task: Remove `print()` statements once fixed.
- [ ] Task: Conductor - User Manual Verification 'End-to-End Test'
