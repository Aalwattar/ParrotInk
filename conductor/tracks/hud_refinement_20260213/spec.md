# Track Specification: HUD Visual & Behavioral Overhaul

**Goal:** Modernize the Floating Indicator (HUD) to be a non-intrusive "Live Preview" that provides clear status feedback without redundant text echoes.

## 1. Visual Design (Geometry)
- **Position:** Bottom-Center (e.g., 100px from bottom edge).
- **Height:** Reduced (~34px).
- **Corners:** Modern rounded rect (10px radius).
- **Width:** Dynamic (min 200px, max 600px).
- **Aesthetics:** Acrylic/Glass background, centered text.

## 2. Behavioral Logic (The "Source of Truth")

### A. Partial vs. Final
- **Rule:** The HUD shows **Partial Preview Only**.
- **Constraint:** On `final` event, the HUD must **NOT** replace the preview text with the final transcript.
- **Rationale:** The final text appears in the application; showing it in the HUD is redundant and confusing.

### B. Status Signaling
- **States:**
    1.  `Connecting...` (Warmup/Reconnect)
    2.  `Listening...` (Active, no text yet)
    3.  `[Partial Text]` (Active, speech detected)
    4.  `Finalized ✅` (Brief flash on final result)
    5.  `Error ❌` (On failure)

- **Final Flash:**
    - When a final result arrives, show a "Finalized" state/icon.
    - Duration: **200ms**.
    - After flash, hide immediately (if stopped).

### C. Timing & Anti-Flicker
- **Minimum Visible Time:** Once shown, HUD must stay visible for at least **300ms**, even if the user stops immediately.
- **Throttle:** Limit redraws to **20 FPS** (50ms interval) to reduce jitter.

## 3. Scope
- `engine/hud_renderer.py` (Skia implementation - Primary logic).
- `engine/indicator_ui.py` (Wrapper / GDI fallback).
- `engine/ui_bridge.py` (Remove the 300ms partial suppression, as it conflicts with the new "Preview Only" logic).

## 4. Success Criteria
- [ ] HUD appears bottom-center with new geometry.
- [ ] HUD never displays the "Final" text string (only partials).
- [ ] "Finalized ✅" flash appears for ~200ms on completion.
- [ ] HUD does not "blink" (min visible 300ms).
- [ ] Redraws are smooth (throttled).
