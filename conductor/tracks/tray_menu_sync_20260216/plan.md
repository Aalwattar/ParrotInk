# Implementation Plan: Tray Menu Hotkey Label Sync

This track addresses the bug where the tray menu label for "Change Hotkey" does not update immediately after a change.

## Phase 1: Investigative Trace
- [x] Task: Audit `engine/ui.py` to see how the menu is constructed. [checkpoint: 37d995c]
    - [x] Determine if the menu items are static or if they are regenerated on each right-click. (Found: Static reconstruction via `_create_icon` during init, uses lambdas for dynamic labels but `pystray` needs manual trigger to refresh on Windows).
    - [x] Identify if `pystray` supports dynamic label updates for existing menu items. (Found: Assigning `self.icon.menu = self._create_menu()` is the reliable way).
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Implementation & TDD
- [x] Task: Create a reproduction test for menu label sync. [checkpoint: 2027c5f]
- [x] Task: Implement the refresh logic in `engine/ui.py`. [checkpoint: 2027c5f]
- [x] Task: Verify fix with reproduction test. [checkpoint: 2027c5f]
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Final Validation
- [x] Task: Run full "Definition of Done Gate". [checkpoint: 2027c5f]
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase: Review Fixes
- [x] Task: Apply review suggestions [checkpoint: e169a9f]
