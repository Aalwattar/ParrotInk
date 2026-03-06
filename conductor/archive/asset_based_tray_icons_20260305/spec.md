# Specification: Asset-Based Tray Icons

## 1. Overview
This track replaces the current dynamically generated colored square tray icons with custom `.ico` assets. The goal is to provide a more professional visual identity and clear state feedback, moving away from simple squares that users sometimes mistake for system status indicators (like Task Manager).

## 2. Functional Requirements

### 2.1 Asset Management
- **Location:** All new tray icon assets MUST be placed in `assets/icons/`.
- **Format:** The application will use `.ico` files provided by the user.
- **File Naming (State-based):**
  - `tray_idle.ico`
  - `tray_listening.ico`
  - `tray_connecting.ico`
  - `tray_error.ico`
  - `tray_transition.ico` (For 'Stopping' or 'Shutting Down' states)

### 2.2 Icon Loading & Logic
- **Efficient Loading:** Icons should be loaded/cached at startup to ensure high-performance switching between states.
- **State Mapping:** The `UI` class MUST map internal `AppState` values to the corresponding file assets.
- **Robust Fallback:** If a specific `.ico` file is missing from the `assets/icons/` directory, the application MUST automatically fall back to the original dynamic colored-square generation logic. This ensures the tray icon never disappears.

## 3. Non-Functional Requirements
- **Reliability:** The icon switching logic must be "production-ready," meaning it handles file system access safely and doesn't crash if assets are tampered with.
- **Aesthetics:** Using custom icons improves the overall "Fluent" look and feel of the application on Windows.

## 4. Out of Scope
- Changing the actual design of the icons (to be provided by the user).
- Modifying the HUD or other UI elements outside the system tray icon itself.
