# Implementation Plan: Auto-Select Provider and Refine Error Message

## Phase 1: Refine Error Messaging
- [x] Task: Locate the existing missing API key error message generation (likely within `engine/connection.py`, `main.py`, or `engine/ui_bridge.py`). [07ec315]
- [x] Task: Write failing unit test(s) verifying the exact new error message is emitted when an API key is missing. [07ec315]
- [x] Task: Update the error message to the exact string: `"Provider Missing API Key. Right-click Tray Icon > Settings to configure."` [07ec315]
- [x] Task: Run `uv run pytest -q` to ensure all tests pass. [07ec315]
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Refine Error Messaging' (Protocol in workflow.md)

## Phase 2: Implement Startup Auto-Selection
- [x] Task: Write failing unit test(s) (e.g., in `tests/test_availability.py` or a new test file) asserting that initializing the application with one specific valid key automatically updates the configured provider to match that key, while leaving it unchanged if zero or multiple keys exist. [07ec315]
- [x] Task: Implement the auto-selection logic during application startup. This should likely happen right after the `AppCoordinator` evaluates initial provider availability, before the main UI loop starts. If the current provider is invalid AND exactly one other provider is valid, switch the provider via `config.update_and_save(...)`. [07ec315]
- [x] Task: Run `uv run pytest -q` to ensure all tests pass. [07ec315]
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Implement Startup Auto-Selection' (Protocol in workflow.md)

## Phase 3: Implement Dynamic Auto-Selection
- [x] Task: Write failing unit test(s) verifying that dynamically setting or removing an API key (which leaves exactly one valid provider) triggers a provider switch if the current provider is invalid. [07ec315]
- [x] Task: Update the `on_set_key` callback (in `engine/gui_main.py` or similar) to evaluate the new global availability state after a key is saved. Apply the same auto-switch logic used in Phase 2 if the conditions are met. [07ec315]
- [x] Task: Verify the UI (Tray Menu and HUD) correctly reflects the dynamically switched provider. [07ec315]
- [ ] Task: Run the 'Definition of Done Gate' (`ruff`, `mypy`, `pytest`) to ensure codebase integrity.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Implement Dynamic Auto-Selection' (Protocol in workflow.md)
