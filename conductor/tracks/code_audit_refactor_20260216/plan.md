# Implementation Plan: Code Audit & Refactoring

This track follows a module-by-module audit and refactor workflow.

## Phase 1: Audit & Refactor - Core Engine (`main.py`, `engine/connection.py`, `engine/config.py`)
- [x] Task: **Audit**: Core Engine.
- [x] Task: **Report**: Present findings for Core Engine to user for approval.
- [x] Task: **Refactor**: Core Engine (Only after approval). [200d639]
    - [x] Wire up neglected config items.
    - [x] Consolidate constants.
    - [x] Cleanup imports and dead code.
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Audit & Refactor - Audio Pipeline (`engine/audio/`)
- [ ] Task: **Audit**: Audio Pipeline.
    - [ ] Check chunk sizes, sample rates, and buffer logic for hardcoded values.
    - [ ] Verify if all audio-related config items are respected.
- [ ] Task: **Report**: Present findings for Audio Pipeline to user for approval.
- [ ] Task: **Refactor**: Audio Pipeline (Only after approval).
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Audit & Refactor - UI & HUD (`engine/ui.py`, `engine/indicator_ui.py`, `engine/hud_renderer.py`)
- [ ] Task: **Audit**: UI & HUD.
    - [ ] Audit colors, font sizes, offsets, and polling intervals.
    - [ ] Identify tight coupling or duplicate logic between indicator and tray.
- [ ] Task: **Report**: Present findings for UI & HUD to user for approval.
- [ ] Task: **Refactor**: UI & HUD (Only after approval).
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase 4: Audit & Refactor - Platform & Utilities (`engine/platform_win/`, `engine/injection.py`, etc.)
- [ ] Task: **Audit**: Platform & Utilities.
    - [ ] Check Windows API constants and injection timings.
- [ ] Task: **Report**: Present findings for Platform & Utilities to user for approval.
- [ ] Task: **Refactor**: Platform & Utilities (Only after approval).
- [ ] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)

## Phase 5: Final Global Sweep & DoD Gate
- [ ] Task: Run full "Definition of Done Gate" across the entire project.
    - [ ] `uv run ruff check .`
    - [ ] `uv run ruff format --check .`
    - [ ] `uv run mypy .`
    - [ ] `uv run pytest -q`
- [ ] Task: Conductor - User Manual Verification 'Phase 5' (Protocol in workflow.md)
