# Implementation Plan: HUD Health Watchdog

## Phase 1: Implement Win32 Responsiveness Probe
- [ ] Task: Add `is_responsive()` method to `HudOverlay` in `engine/hud_renderer.py`.
- [ ] Task: Define `HUD_HEALTH_TIMEOUT_MS = 50` as an internal constant in `engine/hud_renderer.py`.
- [ ] Task: Implement logic using `win32gui.SendMessageTimeout` with `win32con.WM_NULL` and `win32con.SMTO_ABORTIFHUNG`.
- [ ] Task: Ensure the method returns `False` if `self._hwnd` is None or the timeout occurs.

## Phase 2: Bridge to Indicator Controller
- [ ] Task: Add `is_healthy()` method to `IndicatorWindow` in `engine/indicator_ui.py`.
- [ ] Task: Implement the check: return `True` for `GdiFallbackWindow`, otherwise call `self.impl.is_responsive()`.
- [ ] Task: Add logging to capture when a HUD is detected as unhealthy.

## Phase 3: Update Supervisor Recovery
- [ ] Task: Update `TrayApp._ensure_indicator` in `engine/ui.py`.
- [ ] Task: Replace `getattr(self.indicator, "is_alive", True)` with `self.indicator.is_healthy()`.
- [ ] Task: Verify that the `stop()` call on a dead indicator is still safely wrapped in a try/except block.

## Phase 4: Verification
- [ ] Task: Create a reproduction script `tests/repro_hud_hang.py` that simulates a frozen message pump.
- [ ] Task: Verify that triggering a HUD update (e.g., via `UIBridge`) forces a restart of the HUD.
- [ ] Task: Run the 'Definition of Done Gate' (`ruff`, `mypy`, `pytest`).
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Verification' (Protocol in workflow.md)
