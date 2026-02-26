# Track: RTL & Arabic Shaping Support in HUD

## 1. Objective
Enable correct rendering of Right-to-Left (RTL) text and Arabic character shaping (joining) in the Skia-based floating HUD.

## 2. Problem Analysis
- **Observed Behavior:** Arabic text is displayed in a "messed up" way in the HUD. Characters appear one-by-one in the wrong direction and are not joined (shaped) correctly.
- **Root Cause:** The `GlassStyle.draw` method in `engine/hud_styles.py` uses `skia.TextBlob.MakeFromString`, which is a low-level primitive that does not support BiDi (Bidirectional) layout or complex script shaping (Arabic, Devanagari, etc.).

## 3. Implementation Plan

### Phase 1: Research & Tooling
- [x] Verify if `skia-python`'s `Shaper` or `paragraph` module is available in the current environment. (Confirmed: `skia.textlayout` available)
- [x] Create a standalone Skia script to test Arabic rendering (`Ø§Ù„Ø³Ù„Ø§Ù… Ø¹Ù„ÙŠÙƒÙ…`) with different Skia APIs. (Done: `tests/test_arabic_rendering.py` created and tested)

### Phase 2: Refactor Drawing Logic
- [ ] Replace `skia.TextBlob` with a more robust text layout engine (e.g., `skia.Shaper` or `skia.textlayout.ParagraphBuilder`).
- [ ] Update `GlassStyle.draw` to handle RTL alignment and shaping.
- [ ] Ensure the capsule width calculation correctly accounts for shaped text width.

### Phase 3: Verification
- [ ] Test with Arabic, English, and Mixed-direction text.
- [ ] Ensure no regressions in performance or memory usage.
- [ ] Run DoD Gate: ruff, mypy, pytest.

## 4. References
- Skia Shaper: Handles BiDi and Unicode shaping.
- Skia Paragraph: Higher-level text layout module.
