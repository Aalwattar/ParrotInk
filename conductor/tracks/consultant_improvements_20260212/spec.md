# Track Specification: Consultant Security & Stability Improvements

## Overview
Apply a set of critical security and stability improvements identified by a consultant. These changes focus on resource management, security best practices, and event loop reliability without altering core user-facing functionality.

## 1. Functional Scope

### 1.1 Unified Input Monitoring (C1)
- **Goal:** Consolidate multiple keyboard listeners into a single managed hook.
- **Scope:** 
    - Merge `gui_main.py` hotkey listener and `interaction.py` "stop on any key" listener.
    - Create a central `InputMonitor` (likely in `engine/interaction.py` or a new utility) that routes events thread-safely to the `AppCoordinator`.

### 1.2 Logging Lifecycle Management (C2)
- **Goal:** Prevent shutdown hangs and resource leaks in the logging system.
- **Scope:**
    - Implement `shutdown_logging()` in `engine/logging.py` to stop the `QueueListener`.
    - Ensure `shutdown_logging()` is called during `AppCoordinator.shutdown` and any application exit path.

### 1.3 Secure Credential Entry (C3)
- **Goal:** Prevent API keys from being echoed in the terminal.
- **Scope:**
    - Update `engine/credential_ui.py` to use `getpass.getpass()` for console input.
    - Maintain fallback behavior with explicit warnings if `getpass` is unavailable.

### 1.4 Eval Mode Reliability (C4)
- **Goal:** Ensure `eval_main.py` terminates correctly when work is finished.
- **Scope:**
    - Update `EvalCoordinator` to set `finished_event` immediately upon receiving a final transcript.
    - Remove reliance on 5-second grace periods/timeouts for standard termination.

## 2. Technical Goals
- **Stability:** Eliminate race conditions between multiple low-level hooks.
- **Safety:** Align with security standards for sensitive data input.
- **Clean Shutdown:** Ensure zero background threads are leaked on exit.

## 3. Acceptance Criteria
- [ ] No more than one active `pynput.keyboard.Listener` instance exists at any time.
- [ ] Application shuts down cleanly in < 1 second after exit command.
- [ ] API keys entered in console are not echoed (masked/invisible).
- [ ] `eval_main.py` finishes as soon as the final transcript is received.
- [ ] Passes the "Definition of Done" Gate (ruff, mypy, pytest).
