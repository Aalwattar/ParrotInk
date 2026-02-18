# Implementation Plan: Startup Toast Notification

## Phase 1: Environment Preparation [checkpoint: 5203a17]
- [x] Task: Add `win11toast` dependency to `pyproject.toml` c47924a
- [x] Task: Update `conductor/tech-stack.md` to include `win11toast` a961108
- [x] Task: Run `uv sync` to install dependencies 62afaad
- [x] Task: Conductor - User Manual Verification 'Environment Preparation' (Protocol in workflow.md)

## Phase 2: Notification Implementation (TDD) [checkpoint: 09f17d9]
- [x] Task: Create `tests/test_notifications.py` with failing tests c8e1476
    - [x] Mock `win11toast.toast`
    - [x] Test that notification is triggered with correct dynamic content (hotkey)
    - [x] Test that notification is NOT triggered when `--background` is present
- [x] Task: Implement notification logic in `engine/ui_utils.py` c8e1476
    - [x] Create `show_startup_toast(config: Config)` function
- [x] Task: Integrate notification into `main.py` c8e1476
    - [x] Call `show_startup_toast` in the standard execution block if `not cli_args.background`
- [x] Task: Verify implementation by passing all tests c8e1476
- [x] Task: Conductor - User Manual Verification 'Notification Implementation' (Protocol in workflow.md)

## Phase 3: Quality Assurance & "Done" Gate
- [ ] Task: Run project-wide linting and formatting
    - [ ] `uv run ruff check --fix .`
    - [ ] `uv run ruff format .`
- [ ] Task: Run type checking
    - [ ] `uv run mypy .`
- [ ] Task: Final test execution
    - [ ] `uv run pytest -q`
- [ ] Task: Conductor - User Manual Verification 'Final Quality Gate' (Protocol in workflow.md)
