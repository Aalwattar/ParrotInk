# Track Specification: Debug Silent Failure

## Overview
Investigate and resolve the critical issue where "Start Listening" is logged, but the connection process hangs silently without error or further progress.

## 1. Functional Scope

### 1.1 Instrumentation
- **Goal:** Trace execution flow with 100% certainty.
- **Action:** Add `print()` statements (flush=True) to `AppCoordinator.start_listening`, `ConnectionManager.ensure_connected`, and `AudioStreamer.start`.
- **Why:** To rule out logging queue deadlocks or buffering issues.

### 1.2 Isolation
- **Goal:** Identify the blocking call.
- **Suspects:**
    - `Anchor.capture_current` (even with ctypes, maybe specific call hangs?)
    - `ConnectionManager.ensure_connected` (awaiting provider start?)
    - `AudioStreamer` initialization (sounddevice locking?)

## 2. Technical Goals
- **Root Cause Identified:** Pinpoint the exact line of code where execution stops.
- **Fix Implemented:** Resolve the hang/block.
- **Verification:** Ensure dictation works end-to-end.

## 3. Acceptance Criteria
- [ ] Application connects to OpenAI/AssemblyAI successfully.
- [ ] Audio pipeline processes chunks.
- [ ] "Ensuring connection..." and subsequent logs appear in console.
