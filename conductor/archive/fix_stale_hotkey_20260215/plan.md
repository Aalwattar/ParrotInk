# Implementation Plan: fix_stale_hotkey_20260215

This track addresses the bug where the hotkey listener stops working after keys get "stuck" (missed release events) during system lag or long idle periods.

## Phase 1: Robust Hotkey Recovery
- [ ] Task: Implement Stale Key Eviction in `AppCoordinator.on_press`.
    - [ ] Update `main.py`.
    - [ ] Move staleness check to the beginning of `on_press`.
    - [ ] Automatically evict keys with timestamps older than 3 seconds.
    - [ ] Reset `hotkey_pressed` if all hotkey keys are stale.
- [ ] Task: Verify with reproduction script.
    - [ ] Run `python tests/repro_stale_hotkey.py`.

## Phase 2: Final Validation and Done Gate
- [ ] Task: Run full "Definition of Done Gate":
    - [ ] `uv run ruff check .`
    - [ ] `uv run ruff format --check .`
    - [ ] `uv run mypy .`
    - [ ] `uv run pytest -q`
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)
