# Specification: HUD Health Watchdog

## 1. Overview
The floating HUD (`IndicatorWindow`) occasionally fails to appear after a system restart or when the Windows desktop is not fully initialized. The current health check `getattr(self.indicator, "is_alive", True)` is insufficient because it only checks Python thread existence, not Win32 window responsiveness. This track implements a robust health check using `SendMessageTimeout` to detect and recover from hung or failed HUD instances.

## 2. Functional Requirements

### 2.1 Win32 Responsiveness Probe
- **Implementation**: Add a method to `HudOverlay` in `engine/hud_renderer.py` that sends a `WM_NULL` message to the window handle (`_hwnd`).
- **Safety Flags**: Must use `win32gui.SendMessageTimeout` with `SMTO_ABORTIFHUNG` to fail immediately if Windows knows the window is hung.
- **Timeout**: Use an internal constant of **50ms**.
- **Detection**: If the call fails, times out, or the `_hwnd` is missing, the window is considered "unhealthy".

### 2.2 Bridge and Supervisor Update
- **Bridge**: Update `IndicatorWindow` in `engine/indicator_ui.py` to expose an `is_healthy()` method that delegates to the underlying `HudOverlay`.
- **Supervisor**: Update `TrayApp._ensure_indicator` in `engine/ui.py` to replace the naive `getattr` check with the new `is_healthy()` call.

### 2.3 Lazy Recovery
- **Frequency**: The check MUST be performed on-demand within `_ensure_indicator` whenever a HUD update is requested (e.g., when recording starts or text is updated).
- **Recovery**: If a HUD is detected as unhealthy, the supervisor MUST discard the stale reference and initialize a new one.

## 3. Non-Functional Requirements
- **Performance**: The check must be near-instant (<50ms worst case) and non-blocking for the main application thread.
- **Resilience**: The check must correctly handle cases where the HUD is still in its startup retry loop.

## 4. Acceptance Criteria
- [ ] Manual verification: Simulate a hung HUD thread and verify it restarts automatically when the hotkey is pressed.
- [ ] Code check: Ensure no `asyncio.Lock` or `threading.Lock` is held during the `SendMessageTimeout` call.
- [ ] No regression: Standard HUD behavior (animation, partials) remains smooth.

## 5. Out of Scope
- Moving the HUD to a separate process.
- Implementing a proactive background watchdog (on-demand only).
