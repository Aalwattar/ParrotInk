# Implementation Plan: Single Instance Protection

Prevent multiple instances of the application from running simultaneously to avoid hotkey conflicts and hardware resource (microphone) contention.

## Phase 1: Win32 Mutex Implementation
Goal: Use a named mutex to detect an existing process.

- [x] Task: Create `engine/platform_win/instance.py`. [16d8a83]
- [x] Task: Implement `SingleInstance` class to hold the mutex handle globally. [16d8a83]
- [x] Task: Use `CreateMutexW` and check `GetLastError() == ERROR_ALREADY_EXISTS` (183) for detection. [16d8a83]
- [x] Task: Ensure the mutex handle is **never closed** until the process exits. [16d8a83]

## Phase 2: Integration & User Feedback
Goal: Exit gracefully with a notification if already running.

- [x] Task: Integrate check into `main.py` entry point. [35f6979]
- [x] Task: If already running, show a Win32 `MessageBoxW` with the message: "Voice2Text is already running. Please check the system tray icon." [35f6979]
- [x] Task: (Optional) Support `--background` flag to suppress the message box if launched via automation. [35f6979]
- [x] Task: Conductor - User Manual Verification 'Single Instance'

## Phase 3: Verification
Goal: Ensure zero regressions.

- [x] Task: Run full test suite. [439a3f2]
- [x] Task: Pass DOD Gate. [439a3f2]
