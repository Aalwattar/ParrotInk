# Implementation Plan: HUD Visual & Behavioral Overhaul

- [x] **Step 1: Visual Geometry (Skia & GDI)**
    - Modify `hud_renderer.py`: Update `paint()` for 10px radius, smaller height, bottom-center positioning.
    - Modify `indicator_ui.py`: Update GDI fallback drawing for similar geometry.

- [x] **Step 2: Logic Refactor (IndicatorWindow)**
    - Modify `IndicatorWindow` in `indicator_ui.py`:
        - Add `_shown_at` timestamp for Min Visible Time (300ms).
        - Add `_final_flash_until` timestamp for Flash Logic.
        - Add `_last_redraw_at` for throttling (20fps).
    - **CRITICAL:** Change `on_final` to *not* call `update_partial_text`. Instead, set the "Finalized" state/icon.

- [x] **Step 3: Renderer State Support**
    - Update `HudOverlay` (and GDI fallback) to accept/render specific states:
        - `Connecting`, `Listening`, `Finalized` (with icon).
    - Ensure `Finalized` state overrides the text display.

- [x] **Step 4: Cleanup Bridge**
    - Modify `ui_bridge.py`: Remove or relax the 300ms "Partial Suppression" logic since we no longer echo finals in the HUD.

- [x] **Step 5: Verification**
    - Verify positioning.
    - Verify "Finalized" flash (no text echo).
    - Verify anti-flicker on short utterances.
