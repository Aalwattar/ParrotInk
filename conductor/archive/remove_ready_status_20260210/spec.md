# Specification: Remove Redundant Tray Status Item

## 1. Overview
The system tray menu currently contains a static, disabled menu item labeled "Status: Ready" followed by a separator. Since the application state is already communicated via the tray icon color (Black for Idle, Red for Recording, Orange for Error), this text label is redundant and adds unnecessary clutter to the menu.

## 2. Functional Requirements
- **Remove Status Label:** Remove the `pystray.MenuItem("Status: Ready", ...)` entry from the `TrayApp._create_icon` method in `engine/ui.py`.
- **Remove Leading Separator:** Remove the `pystray.Menu.SEPARATOR` that immediately follows the status label.

## 3. Acceptance Criteria
1.  **Menu Cleanliness:** When right-clicking the system tray icon, the menu should start directly with the provider selection options ("OpenAI", "AssemblyAI").
2.  **No Functional Loss:** All other menu items (Provider selection, Credentials, Open Config, Quit) must remain functional and correctly positioned.
