# Fix Plan: HUD Newlines and Multi-Line Injection

**Goal:** Remove newlines from HUD display while ensuring robust newline injection in target applications (CMD, Browsers, etc.).

**Analysis:**
1.  **HUD Newlines:** The HUD (Skia-based) isn't designed for multiline and newlines look messy. We should replace `\n` with spaces just for the HUD.
2.  **Injection Newlines:** Some applications (like CMD) don't process the Unicode `\n` character as an "Enter" key. We need to explicitly send `VK_RETURN` when a newline is encountered.

**Architecture:**
- **`engine/indicator_ui.py`**: Sanitize text in `_render_preview` to replace `\n` with spaces.
- **`engine/injector.py`**: Update `inject_text` to handle `\n` by sending `VK_RETURN`.

### Task 1: Sanitize HUD Text
**File:** `engine/indicator_ui.py`
- Modify `_render_preview` to replace `\n` in `committed` and `partial` with spaces.

### Task 2: Robust Newline Injection
**File:** `engine/injector.py`
- Modify `inject_text` to detect `\n` and use `VK_RETURN`.

### Task 3: Verification
- Manual verification in CMD and Browser.
- DOD Gate (Ruff, Mypy, Pytest).
