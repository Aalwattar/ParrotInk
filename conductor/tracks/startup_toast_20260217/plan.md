# Implementation Plan: Startup Toast Notification

## Phase 1: Environment Preparation
- [x] Task: Add `win11toast` dependency to `pyproject.toml` c47924a
- [ ] Task: Update `conductor/tech-stack.md` to include `win11toast`
- [ ] Task: Run `uv sync` to install dependencies
- [ ] Task: Conductor - User Manual Verification 'Environment Preparation' (Protocol in workflow.md)

## Phase 2: Notification Implementation (TDD)
- [ ] Task: Create `tests/test_notifications.py` with failing tests
    - [ ] Mock `win11toast.toast`
    - [ ] Test that notification is triggered with correct dynamic content (hotkey)
    - [ ] Test that notification is NOT triggered when `--background` is present
- [ ] Task: Implement notification logic in `engine/ui_utils.py`
    - [ ] Create `show_startup_toast(config: Config)` function
- [ ] Task: Integrate notification into `main.py`
    - [ ] Call `show_startup_toast` in the standard execution block if `not cli_args.background`
- [ ] Task: Verify implementation by passing all tests
- [ ] Task: Conductor - User Manual Verification 'Notification Implementation' (Protocol in workflow.md)

## Phase 3: Quality Assurance & "Done" Gate
- [ ] Task: Run project-wide linting and formatting
    - [ ] `uv run ruff check --fix .`
    - [ ] `uv run ruff format .`
- [ ] Task: Run type checking
    - [ ] `uv run mypy .`
- [ ] Task: Final test execution
    - [ ] `uv run pytest -q`
- [ ] Task: Conductor - User Manual Verification 'Final Quality Gate' (Protocol in workflow.md)
