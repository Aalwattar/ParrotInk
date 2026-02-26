# Track: HUD Startup Recovery & Error Handling

## 1. Objective
Ensure the floating HUD (IndicatorWindow) correctly initializes and recovers if it fails to start during the initial application boot (especially after system restarts or crashes).

## 2. Problem Analysis
- **Observed Behavior:** The HUD sometimes fails to appear after a system restart, even if the application is otherwise functional. Toggling "Show HUD" in the tray menu does not fix it if it failed at startup.
- **Root Causes (Suspected):**
  - `TrayApp.__init__` only attempts to create the `IndicatorWindow` once. If it fails (due to libraries not being ready, or Windows desktop not being fully initialized), it remains `None`.
  - `IndicatorWindow` wraps `HudOverlay`, which runs in a background thread. If `HudOverlay.run()` crashes, the thread exits silently.
  - `on_toggle_hud` only updates the configuration; it does not attempt to recreate the `IndicatorWindow` if it is currently `None`.

## 3. Implementation Plan

### Phase 1: Research & Reproduction
- [x] Create a reproduction script that mocks a failed `HudOverlay` initialization. e81240d
- [x] Add enhanced logging to `HudOverlay.run()` and `IndicatorWindow.__init__` to capture specific Win32 errors (e.g., `CreateWindowEx` failures). e81240d

### Phase 2: Lazy Re-initialization
- [x] Refactor `TrayApp` to support lazy re-initialization of `self.indicator`. c53326d
- [x] Update `on_toggle_hud` to attempt creating the `IndicatorWindow` if it's currently `None` and being enabled. c53326d

### Phase 3: Startup Robustness
- [x] Implement a "Desktop Ready" check or a short delay/retry mechanism for `HudOverlay.run()`. a125d14
- [x] Ensure that if `HudOverlay.run()` exits unexpectedly, it logs the error and allows for a manual restart via the UI toggle. a125d14

## 4. Verification
- [ ] Verify that disabling/enabling the HUD via the tray menu can recover a missing HUD.
- [ ] Simulate a system-start delay and verify the HUD eventually appears.
- [ ] Run DoD Gate: ruff, mypy, pytest.
