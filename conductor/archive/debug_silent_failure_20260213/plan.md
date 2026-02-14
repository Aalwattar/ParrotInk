# Implementation Plan: Debug Silent Failure

Instrument and fix the connection hang.

## Phase 1: Instrumentation
Goal: Visualize the hang.

- [x] Task: Add `print(..., flush=True)` to `main.py` -> `start_listening`.
- [x] Task: Add `print(..., flush=True)` to `engine/connection.py` -> `ensure_connected`.
- [x] Task: Add `print(..., flush=True)` to `engine/anchor.py` -> `capture_current`.
- [x] Task: Conductor - User Manual Verification 'Check Prints'

## Phase 2: Fix & Cleanup
Goal: Resolve the issue based on findings (likely removing the blocking call).

- [x] Task: If Anchor hangs: Disable anchor or fix ctypes usage.
- [x] Task: If Connection hangs: Check `websockets` or network timeout.
- [x] Task: Remove `print()` statements once fixed.
- [x] Task: Conductor - User Manual Verification 'End-to-End Test'
