# Specification: Cosmetic & UI Refinements Track

## 1. Overview
This track focuses on modernizing the visual identity of Voice2Text and exposing existing features to the Tray UI for better accessibility. The goal is a "top-tier UX" feel that is crisp, modern, and native to Windows.

## 2. Functional Requirements

### 2.1 Tray Icon Overhaul
- **Design:** Replace the current "ugly" icon with a dynamic, procedural "Modern Square" design.
- **Style:** Crisp square with slight rounded corners (iOS/Fluent style).
- **States:**
    - **Idle:** Neutral color (e.g., Slate Gray or Slate Blue).
    - **Listening:** Vibrant, active color (e.g., "Microsoft Blue" or "Electric Green").
    - **Error:** Warning color (e.g., Soft Orange or Red).
- **Implementation:** Use the `PIL` (Pillow) library to generate these icons at runtime to ensure maximum crispness on High-DPI displays.

### 2.2 HUD Text Enhancements
- **Font:** Standardize on the Windows system font (**Segoe UI**).
- **Size:** Adjust font size to the lower end of the high-readability range (e.g., 14pt-16pt) to ensure it looks integrated and professional, not oversized.
- **Clarity:** Ensure high contrast and clear rendering (using anti-aliasing features of the rendering library).

### 2.3 Feature Exposure (Tray Menu)
- **"Hold to Talk":** Add a new checkable menu item under "Settings". 
    - **Label:** "Hold to Talk".
    - **Functionality:** Toggles the `hotkeys.hold_mode` configuration boolean.
- **Menu Header:** Add a non-clickable (disabled) menu item at the very top of the tray menu.
    - **Format:** `[Product Name] v[Version]` (e.g., "Voice2Text v0.1.5").
    - **Implementation:** Dynamically read the version from `pyproject.toml`.

## 3. Technical Requirements
- **Version Parsing:** Use `tomllib` (or `tomli`) to read `pyproject.toml` safely.
- **Icon Generation:** Refactor `TrayApp._create_image` to support the new square aesthetic.
- **HUD Update:** Update `HUDStyles` and the renderer to use the system font and larger size.

## 4. Acceptance Criteria
- [ ] Tray icon is square with rounded corners and changes color correctly per state.
- [ ] HUD text uses Segoe UI and is visibly larger and clearer than the previous version, yet remains integrated.
- [ ] "Hold to Talk" is toggleable from the Tray and persists to `config.toml`.
- [ ] The Tray menu displays the current version from `pyproject.toml` at the top.
- [ ] No hard-coded version strings in the UI code.

## 5. Out of Scope
- Major architectural changes to the transcription engine.
- Redesigning the entire configuration file format.
