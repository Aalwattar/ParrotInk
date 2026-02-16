# Implementation Plan: Tray Menu Hotkey Label Sync

This track addresses the bug where the tray menu label for "Change Hotkey" does not update immediately after a change.

## Phase 1: Investigative Trace
- [ ] Task: Audit `engine/ui.py` to see how the menu is constructed.
    - [ ] Determine if the menu items are static or if they are regenerated on each right-click.
    - [ ] Identify if `pystray` supports dynamic label updates for existing menu items.
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Implementation & TDD
- [ ] Task: Create a reproduction test for menu label sync.
    - [ ] **Red Phase**: Write a test in `tests/test_tray_sync.py` that simulates a hotkey change and asserts the `TrayApp` menu item text is updated.
    - [ ] Confirm the test fails.
- [ ] Task: Implement the refresh logic in `engine/ui.py`.
    - [ ] **Green Phase**: Either call `self.icon.update_menu()` (if supported) or trigger a full menu rebuild when the `config` is updated.
    - [ ] Ensure the update is triggered via the `UIBridge` to maintain thread safety.
- [ ] Task: Verify fix with reproduction test.
    - [ ] Rerun `tests/test_tray_sync.py` and confirm it passes.
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Final Validation
- [ ] Task: Run full "Definition of Done Gate".
    - [ ] `uv run ruff check .`
    - [ ] `uv run ruff format --check .`
    - [ ] `uv run mypy .`
    - [ ] `uv run pytest -q`
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)
