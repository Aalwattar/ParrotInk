# Specification: Tray Menu Optimization & Hotkey Bug Fix

## 1. Overview
This track addresses three main areas concerning the application's system tray menu:
1. **UI/UX Redesign:** Reviewing and reorganizing the tray menu into a cleaner, more intuitive structure using expert UI/UX principles, balancing sub-menus and flat structures.
2. **Code Review & Conditional Refactoring:** Reviewing the existing menu creation logic. If the code is overblown or poorly organized, extract it into a dedicated, focused module (e.g., `tray_menu.py`). If it is already well-organized, skip the refactor.
3. **Hotkey Bug Resolution:** Investigating and fixing a bug where the application's hotkey resets to its default value on startup (especially after updates). The working theory is that the tray menu initializes with default values and prematurely saves them back to `config.toml`, overwriting user settings.

## 2. Functional Requirements

### 2.1 UI/UX Redesign (The "Clean Menu" Initiative)
- The tray menu MUST be restructured to reduce visual clutter and cognitive load while retaining all necessary functionality.
- **Proposed Revised Structure:**
  - `[Version Header]` (e.g., "ParrotInk v1.0.0" - Clickable if update available)
  - `---`
  - `Providers ⏵` (Sub-menu)
    - `OpenAI` (Radio)
    - `AssemblyAI` (Radio)
  - `Settings ⏵` (Sub-menu)
    - `Hold to Talk` (Checkbox)
    - `Set Hotkey...`
    - `Latency Profile` -> `Fast`, `Balanced`, `Accurate`
    - `Mic Profile` -> `Headset`, `Laptop`, `None`
  - `Tools ⏵` (Sub-menu)
    - `Statistics`
    - `Open Configuration`
    - `Reload Configuration`
    - `Open Log Folder`
  - `---`
  - `Help` (Link to docs/repo)
  - `Check for Updates` (Manual trigger)
  - `---`
  - `Exit`

### 2.2 Code Review & Conditional Refactoring
- **Review Phase:** Analyze the current implementation of the tray menu (likely in `ui.py` or similar).
- **Decision:** If the logic is intertwined with core engine components or exceeds reasonable length, extract the menu construction logic into a dedicated module.
- If extracted, the new module should expose a clean interface for instantiating the menu and binding callbacks. If the current implementation is deemed clean and optimal, document this finding and skip the structural refactor.

### 2.3 Hotkey State Bug Fix
- **Investigation Phase:** Debug the application startup sequence to confirm whether the tray menu initialization or another component is inadvertently triggering a save operation with default values, thus overwriting `config.toml`.
- **Resolution Phase:**
  - Ensure the application strictly reads the hotkey from `config.toml` during initialization.
  - The tray menu MUST NOT push its initial default state back to the configuration file.
  - State changes that trigger a save should ONLY occur via explicit user interaction.

## 3. Non-Functional Requirements
- **Performance:** Reorganizing the menu into sub-menus should not introduce noticeable lag.
- **Stability:** Any UI changes or refactoring must preserve all existing menu functionality.

## 4. Out of Scope
- Complete overhaul of the core engine logic outside of its interaction with the tray menu.
