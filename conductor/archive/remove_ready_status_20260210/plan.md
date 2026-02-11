# Implementation Plan: Remove Redundant Tray Status Item

## Phase 1: Cleanup & Verification [checkpoint: 03a4765]
Remove the redundant status label and separator from the tray menu.

- [x] Task: Write a test in `tests/test_ui.py` to verify the menu structure.
    - [x] Add a test that inspects `app.icon.menu` to ensure the first item is a provider selection, not "Status: Ready".
- [x] Task: Remove the "Status: Ready" item and its separator in `engine/ui.py`.
    - [x] Locate `_create_icon` and remove the first two items in the `pystray.Menu` constructor.
- [x] Task: Verify with `pytest`.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Cleanup & Verification' (Protocol in workflow.md)
