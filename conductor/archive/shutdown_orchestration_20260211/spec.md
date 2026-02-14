# Specification: Shutdown Orchestration (Track 3)

## Overview
Implement a centralized, idempotent shutdown orchestration system to ensure the application exits cleanly under all conditions. This prevents "ghost" processes and ensures all resources are released properly.

## Functional Requirements

### 1. Centralized Shutdown Coroutine
- Implement `AppCoordinator.shutdown(reason: str)` as the single source of truth for cleanup.
- **Mandatory Shutdown Order:**
    1. **Stop Listening:** Halt audio flow.
    2. **Stop Provider:** Close session with 2s timeout.
    3. **Stop Audio Capture:** Stop `sounddevice` stream.
    4. **Stop UI:** Stop `pystray` and join thread.
    5. **Exit Main Loop:** Signal loop to stop.

### 2. Signal Interception & Routing
- Catch `SIGINT` (Ctrl+C) and `SIGTERM`.
- Schedule `shutdown()` on the event loop.

### 3. Idempotency
- Ensure `shutdown()` runs exactly once using an `asyncio.Lock` or `Event`.

### 4. Deadlock Prevention & Escape Hatch
- **Step Timeouts:** Wrap each step in `asyncio.timeout(2.0)`.
- **Total Deadline:** Implement a 10s global shutdown deadline.
- **Last-Resort Escape Hatch:** If the total deadline is exceeded, log failures and terminate using `os._exit(1)`. **Note:** This is an escape hatch for hangs, not a normal shutdown path.

## Non-Functional Requirements
- **Stability:** Prevent process hangs on exit.

## Acceptance Criteria
- [ ] Ctrl+C and Tray Exit trigger the full `shutdown()` sequence.
- [ ] Process terminates completely on Windows.
- [ ] Shutdown logic is idempotent.
- [ ] Escape hatch (`os._exit`) is only triggered after the 10s deadline.
