# Implementation Plan: Tray "Open Log Folder" Integration

## Strategy
1.  Identify the log directory using `get_log_dir()` (likely in `engine/logging.py`).
2.  Add a tray menu item "Open Log Folder" in `engine/ui.py`.
3.  Use `os.startfile` to open it in Windows Explorer.

## Proposed Changes

### 1. `engine/logging.py`
-   Ensure `get_log_dir()` is public and available to `engine/ui.py`.

### 2. `engine/ui.py`
-   Add `_on_open_logs_clicked()` method.
-   Insert a new `pystray.MenuItem("Open Log Folder", self._on_open_logs_clicked)` in the `_create_menu` method, perhaps under `Configuration` or at the root of the menu.

## Verification Plan
1.  **Manual Test**: Run the app. Open the tray menu.
    -   Expect: "Open Log Folder" item is visible.
2.  **Manual Test**: Click "Open Log Folder".
    -   Expect: Windows Explorer opens the log directory.

## Phase: Review Fixes
- [x] Task: Apply review suggestions 21b946f
