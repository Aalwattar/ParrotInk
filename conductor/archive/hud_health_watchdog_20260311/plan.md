# Implementation Plan: HUD Health Watchdog

## Phase 1: Implement Win32 Responsiveness Probe
- [x] Task: Add `is_responsive()` method to `HudOverlay` in `engine/hud_renderer.py`. [05c4621]
- [x] Task: Define `HUD_HEALTH_TIMEOUT_MS = 50` as an internal constant in `engine/hud_renderer.py`. [05c4621]
- [x] Task: Implement logic using `win32gui.SendMessageTimeout` with `win32con.WM_NULL` and `win32con.SMTO_ABORTIFHUNG`. [05c4621]
- [x] Task: Ensure the method returns `False` if `self._hwnd` is None or the timeout occurs. [05c4621]

## Phase 2: Bridge to Indicator Controller
- [x] Task: Add `is_healthy()` method to `IndicatorWindow` in `engine/indicator_ui.py`. [05c4621]
- [x] Task: Implement the check: return `True` for `GdiFallbackWindow`, otherwise call `self.impl.is_responsive()`. [05c4621]
- [x] Task: Add logging to capture when a HUD is detected as unhealthy. [05c4621]

## Phase 3: Update Supervisor Recovery
- [x] Task: Update `TrayApp._ensure_indicator` in `engine/ui.py`. [05c4621]
- [x] Task: Replace `getattr(self.indicator, "is_alive", True)` with `self.indicator.is_healthy()`. [05c4621]
- [x] Task: Verify that the `stop()` call on a dead indicator is still safely wrapped in a try/except block. [05c4621]

## Phase 4: Verification
- [x] Task: Create a reproduction script `tests/test_hud_responsiveness.py` that verifies the responsiveness probe. [05c4621]
- [x] Task: Verify that triggering a HUD update (e.g., via `UIBridge`) forces a restart of the HUD. [05c4621]
- [x] Task: Run the 'Definition of Done Gate' (`ruff`, `mypy`, `pytest`). [05c4621]
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Verification' (Protocol in workflow.md)
