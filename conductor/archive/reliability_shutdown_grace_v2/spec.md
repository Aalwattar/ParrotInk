# Product Spec: Reliability & Shutdown Grace v2

**Objective:** Implement a professional Windows-native keyboard hook to resolve the "Stale Hotkey" (lock/unlock) and "Stuck Modifier" (leaked Ctrl) issues.

## 1. Core Problems (Revised)

### 1.1 Desktop Switch Orphanage
- **Root Cause:** Lock (Win+L) switches the OS to the `Winlogon` desktop, detaching `WH_KEYBOARD_LL` hooks.
- **Goal:** Detect `WM_WTSSESSION_CHANGE` via `WTSRegisterSessionNotification` and re-hook upon Unlock.

### 1.2 Stuck Modifiers
- **Root Cause:** When suppressing a combo (e.g., Ctrl+Space), the `Ctrl DOWN` has already reached the app, but `Ctrl UP` is suppressed.
- **Goal:** Inject a synthetic `KEYUP` for all modifiers the moment dictation begins.

### 1.3 Interpretation Finalization Race
- **Root Cause:** Daemon threads attempting to log during interpreter shutdown.
- **Goal:** Use non-daemon threads and explicit `join()` orchestration.

## 2. Technical Strategy

### 2.1 Native Windows Hook (The Consultant's Logic)
- Implement a custom `WH_KEYBOARD_LL` handler using `ctypes`.
- Explicitly track `_pressed_modifiers` and `_state`.
- Mode Support: `MODE_TOGGLE` and `MODE_HOLD`.
- Logic for synthetic `SendInput` for modifier release.

### 2.2 Dedicated Hook Thread
- Create a non-daemon thread that runs a standard Win32 message loop (`GetMessageW`).
- This ensures the hook remains responsive and is easily Joined during shutdown.

### 2.3 Session Monitoring
- Implement a hidden window to listen for `SessionSwitch` events.
- On `WTS_SESSION_UNLOCK`, re-initialize the `InputMonitor`.
