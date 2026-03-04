# Specification: Tray "Open Log Folder" Integration

## Goal
Improve user supportability by providing a direct link to the log files from the tray menu.

## Problem Statement
- Users find it difficult to locate log files in `%AppData%\voice2text\logs`.
- When troubleshooting with support, the first step is usually to ask for logs.

## Proposed Changes
1.  **Menu Addition**:
    -   Add a new menu item: "Open Log Folder" to the system tray.
2.  **Logic Implementation**:
    -   When clicked, the application should use `os.startfile` (on Windows) or `subprocess` to open the directory containing the current log files in the default file explorer.
3.  **Path Resolution**:
    -   Use the existing `get_log_dir()` or equivalent from `engine/logging.py`.

## Success Criteria
- New tray menu item "Open Log Folder" is visible.
- Clicking the item opens the correct folder in Windows Explorer.
