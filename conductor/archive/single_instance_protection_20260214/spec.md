# Track Specification: Single Instance Protection

**Goal:** Prevent multiple instances of the application from running simultaneously to avoid hotkey conflicts and microphone contention.

## 1. Detection Mechanism
- **Tool:** Win32 Named Mutex.
- **API:** `kernel32.CreateMutexW`.
- **Logic:** Check if `kernel32.GetLastError()` returns `ERROR_ALREADY_EXISTS` (183) after creation.
- **Persistence:** The mutex handle must be held globally and never closed until the application exits to maintain the lock.

## 2. User Feedback
- **UI:** Win32 `MessageBoxW`.
- **Message:** "ParrotInk is already running. Please check the system tray icon for the active instance."
- **Title:** "ParrotInk".
- **Icon:** Information (`MB_ICONINFORMATION`).

## 3. CLI Integration
- **Flag:** `--background`.
- **Behavior:** If `--background` is passed, the second instance should exit silently if already running (no MessageBox).

## 4. Scope
- `engine/platform_win/instance.py` (New module for mutex logic).
- `main.py` (Entry point integration).
- `engine/gui_main.py` (CLI flag registration).
