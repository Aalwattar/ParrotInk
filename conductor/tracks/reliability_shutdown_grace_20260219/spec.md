# Product Spec: Reliability & Shutdown Grace

**Objective:** Resolve the "Stale Hotkey" issue (where the app stops responding after several hours) and fix the "Fatal Python error" (daemon thread crash) during shutdown.

## 1. Core Problems

### 1.1 Stale Hotkey Hook
- **Observation:** The `keyboard` library's Windows hook can be detached or timed out by the OS after long periods of inactivity or system state changes.
- **Root Cause:** Low-level Windows hooks require a message loop and can be "silently unhooked" if they don't respond to the OS within a specific timeout (LowLevelHooksTimeout).
- **Goal:** Implement a more robust "Hook Watchdog" or migrate to a more resilient listener structure (like `pynput` with a dedicated thread and restart logic).

### 1.2 Daemon Thread Shutdown Crash
- **Observation:** `Fatal Python error: _enter_buffered_busy: could not acquire lock for <_io.BufferedWriter name='<stdout>'>`
- **Root Cause:** `ui_thread` is marked as `daemon=True`. When the main thread exits (SIGINT), the daemon thread is still running and tries to log/print while the interpreter is finalizing.
- **Goal:** Make `ui_thread` a non-daemon thread and implement a clean `join()` sequence.

## 2. Proposed Changes

### 2.1 Refactor InputMonitor (Reliability)
- **Action:** Transition from `keyboard` to `pynput` for the global listener OR implement a "Heartbeat" that restarts the `keyboard` hooks every 60 minutes.
- **Verification:** Ensure `suppress=True` still works (critical for user experience).

### 2.2 Clean Shutdown Orchestration
- **Action:** 
    - Change `ui_thread` to `daemon=False`.
    - Update `main_gui` to explicitly `stop()` the `TrayApp` and `join()` the `ui_thread`.
    - Ensure `SanitizingFormatter` handles `None` records gracefully if called during finalization.

### 2.3 Signal Handling Optimization
- **Action:** Ensure `SIGINT` is handled consistently across the main loop and the tray app.
