# Implementation Plan: fix_hotkey_connection_20260215

This plan addresses the hotkey misfire regression and the connection timeout robustness.

## Phase 1: Fix Hotkey Logic
- [ ] Task: Reproduce Hotkey Misfire.
    - [ ] Create `tests/repro_hotkey_misfire.py` simulating `Ctrl` -> `Alt` press sequence and asserting no toggle.
- [ ] Task: Audit and Fix `AppCoordinator.on_press`.
    - [ ] The current logic likely uses `.issubset` incorrectly or doesn't check for exact match length.
    - [ ] Modify `main.py` to ensure `start_listening` only triggers if `current_keys == target_hotkey` (or strict subset logic that waits for the final key).
    - [ ] Verify `hold_mode` logic doesn't interfere.
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: AssemblyAI Connection Robustness
- [ ] Task: Update Connection Timeout configuration.
    - [ ] Modify `engine/config.py` (or default values) to increase `connection_timeout_seconds` to 20s.
- [ ] Task: Harden `ConnectionManager.ensure_connected`.
    - [ ] Catch `asyncio.exceptions.CancelledError` specifically during `provider.start()` and wrap it in a more descriptive error.
    - [ ] Ensure `backoff` logic is triggered correctly.
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Final Validation and Done Gate
- [ ] Task: Run full "Definition of Done Gate":
    - [ ] `uv run ruff check .`
    - [ ] `uv run ruff format --check .`
    - [ ] `uv run mypy .`
    - [ ] `uv run pytest -q`
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)
