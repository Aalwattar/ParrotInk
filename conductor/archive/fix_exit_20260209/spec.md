# Track Specification: Fix pystray SystemExit and Double Ctrl+C Responsiveness

## 1. Overview
The current implementation of `Ctrl+C` handling in `main.py` is unresponsive and triggers a `SystemExit` traceback within `pystray`. This track implements a double-confirmation Ctrl+C behavior and moves the `pystray` loop to a background thread to ensure the main thread remains immediately signal-responsive.

## 2. Functional Requirements
- **Double Ctrl+C Confirmation:**
  - **First Ctrl+C:** Must immediately print (flushed) a confirmation message: `Ctrl+C received. Press Ctrl+C again within 3 seconds to exit.`. It MUST NOT stop the app.
  - **Second Ctrl+C (within 3s):** Must begin graceful shutdown and immediately print `Shutting down...` (flushed).
  - **Expiry:** If 3 seconds pass without a second press, the pending state is cleared.
- **Immediate Feedback:** All terminal output related to signals MUST be flushed immediately to avoid perceived lag.
- **Traceback Elimination:** Resolve the `SystemExit` error by signaling `icon.stop()` and allowing threads to join, rather than forcing `sys.exit()`.

## 3. Technical Requirements
- **Threading Model:** 
  - `pystray` icon loop MUST run in a dedicated background thread.
  - The main thread MUST wait on a `shutdown_event` (with a timeout/loop) to remain responsive to `SIGINT`.
- **Signal Handler:** Must be minimal, only updating state (timestamps/events) and printing. It MUST NOT call `sys.exit()`.
- **Shutdown Bound:** Once confirmed, shutdown MUST complete within ≤ 2 seconds. Remaining threads must be daemonized or forced to terminate if they block.

## 4. Acceptance Criteria
- First Ctrl+C prints confirmation immediately; tray icon remains.
- Second Ctrl+C within 3s prints `Shutting down...` immediately, tray icon disappears, and process terminates cleanly.
- No `SystemExit` traceback is visible in the terminal.
- Terminal output appears instantly upon keypress (flushed).

## 5. Out of Scope
- Modifying transcription or audio capture logic.
