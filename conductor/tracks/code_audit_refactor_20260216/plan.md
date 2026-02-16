# Implementation Plan: Code Audit & Refactoring

This track follows a module-by-module audit and refactor workflow.

## Phase 1: Audit & Refactor - Core Engine (`main.py`, `engine/connection.py`, `engine/config.py`) [checkpoint: f98e3ab]
- [x] Task: **Audit**: Core Engine. [200d639]
- [x] Task: **Report**: Present findings for Core Engine to user for approval. [200d639]
- [x] Task: **Refactor**: Core Engine (Only after approval). [a6b89c6]
    - [x] Wire up neglected config items.
    - [x] Consolidate constants.
    - [x] Cleanup imports and dead code.
    - [x] Fix 'Hold to Talk' for multi-key hotkeys. [a6b89c6]
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md) [200d639]

## Phase 2: Audit & Refactor - Audio Pipeline (`engine/audio/`) [checkpoint: a6b89c6]
- [x] Task: **Audit**: Audio Pipeline.
- [x] Task: **Report**: Present findings for Audio Pipeline to user for approval.
- [x] Task: **Refactor**: Audio Pipeline (Only after approval). [a6b89c6]
    - [x] Consolidate internal constants (Queue size, log intervals).
    - [x] Remove deprecated `_normalize_audio`.
    - [x] Cleanup imports and docstrings.
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Audit & Refactor - UI & HUD (`engine/ui.py`, `engine/indicator_ui.py`, `engine/hud_renderer.py`) [checkpoint: 1447fe9]
- [x] Task: **Audit**: UI & HUD.
- [x] Task: **Report**: Present findings for UI & HUD to user for approval.
- [x] Task: **Refactor**: UI & HUD (Only after approval). [1447fe9]
    - [x] Consolidate UI constants (Colors, Dimensions, Intervals).
    - [x] Refactor Linger Logic to be race-condition safe.
    - [x] Cleanup redundant state tracking in `IndicatorWindow`.
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase 4: Audit & Refactor - Platform & Utilities (`engine/platform_win/`, `engine/injection.py`, etc.) [checkpoint: c40dbca]
- [x] Task: **Audit**: Platform & Utilities. [c40dbca]
- [x] Task: **Report**: Present findings for Platform & Utilities to user for approval. [c40dbca]
- [x] Task: **Refactor**: Platform & Utilities (Only after approval). [c40dbca]
    - [x] Global Rename: Voice2Text -> ParrotInk.
    - [x] Consolidate constants (APP_NAME, Mutex, Backspaces).
    - [x] Implement API Key migration logic.
- [x] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)

## Phase 5: Final Global Sweep & DoD Gate
- [ ] Task: Run full "Definition of Done Gate" across the entire project.
    - [ ] `uv run ruff check .`
    - [ ] `uv run ruff format --check .`
    - [ ] `uv run mypy .`
    - [ ] `uv run pytest -q`
- [ ] Task: Conductor - User Manual Verification 'Phase 5' (Protocol in workflow.md)
