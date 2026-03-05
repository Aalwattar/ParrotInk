# Implementation Plan: Tray Menu Optimization & Hotkey Bug Fix

## Phase 1: Investigation & Hotkey Bug Fix [checkpoint: 6364bdd]
- [x] Task: Write failing test to simulate UI initialization triggering a config save. 6364bdd
- [x] Task: Investigate the application startup sequence (in `main.py` and `ui.py`) to identify redundant or premature `save_config` calls. 6364bdd
- [x] Task: Implement fix: Ensure tray menu strictly reads the hotkey from config without writing defaults back during init. 6364bdd
- [x] Task: Update or write unit tests to ensure `save_config` is not called implicitly during UI startup. 6364bdd
- [x] Task: Conductor - User Manual Verification 'Phase 1: Investigation & Hotkey Bug Fix' (Protocol in workflow.md) 6364bdd

## Phase 2: Code Review & Conditional Refactoring [checkpoint: ae20b5f]
- [x] Task: Review the tray menu construction logic (likely `create_menu` or similar in `ui.py`). ae20b5f
- [x] Task: Decision point: If refactoring is justified, create `engine/tray_menu.py` (or similar) and move logic. Document findings if skipped. ae20b5f
- [x] Task: Write/update tests to ensure menu logic still initializes correctly after refactor (or lack thereof). ae20b5f
- [x] Task: Conductor - User Manual Verification 'Phase 2: Code Review & Conditional Refactoring' (Protocol in workflow.md) ae20b5f

## Phase 3: UI/UX Redesign
- [ ] Task: Restructure the tray menu according to the approved spec (Sub-menus for Providers, Settings, Tools).
- [ ] Task: Implement the flat structure items (Help, Check for Updates, Exit).
- [ ] Task: Ensure all existing callbacks and dynamic states (e.g., greyed-out providers, active provider radio button) function correctly in the new nested structure.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: UI/UX Redesign' (Protocol in workflow.md)
