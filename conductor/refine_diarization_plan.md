# Fix Plan: Refine Diarization Display and Injection

**Goal:** Provide single-line formatted text to the HUD (replacing newlines with spaces) and ensure correct multi-line injection to target applications.

**Analysis of the Issue:**
1.  **HUD Issue:** The HUD is designed for single-line scrolling text. Newlines `\n` break its layout or look cramped. We need to strip newlines for the HUD.
2.  **Injection Issue:** The `inject_text` function in `engine/injector.py` uses `KEYBDINPUT` with `KEYEVENTF_UNICODE`. While this works for standard characters, `\n` (ord 10) or `\r` (ord 13) sometimes behave inconsistently depending on the target application (e.g., cmd.exe vs. a browser text area). We need to handle the "Enter" key explicitly during injection.

**Architecture:**
- **SpeakerManager:** Should return the fully formatted string (with newlines) as the source of truth.
- **Provider / Callbacks:** We don't want to change `on_partial` / `on_final` signatures. However, the HUD and Injector are consumers of these callbacks (via `AppCoordinator` / `UIBridge`).
- **Injector:** Update `inject_text` to handle `\n` by sending the actual `VK_RETURN` (0x0D) key press instead of a raw unicode codepoint for newline.
- **HUD:** The UI layer (`ui_bridge.py` or `hud_renderer.py`) should sanitize incoming text by replacing `\n` with ` ` (space) before displaying.

### Task 1: Fix Injector Newlines
**File:** `engine/injector.py`
- Modify `inject_text` to check if `char == '\n'`.
- If `\n`, simulate a `VK_RETURN` press instead of a unicode injection.

### Task 2: Fix HUD Display
**File:** `engine/ui_bridge.py` or `engine/hud_renderer.py` (Need to verify exact path where text is passed to HUD).
- Update the method that updates the HUD text to `.replace('\n', '  ')` (replace newline with spaces for readability).

### Task 3: Verify DOD
- Run `ruff`, `mypy`, `pytest`.
