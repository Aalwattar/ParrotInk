# Implementation Plan: GitHub Update Checker

## Phase 1: API Foundation
- [ ] Task: Research GitHub API schema & confirm rate-limiting headers.
- [ ] Task: Implement `GitHubClient` in `engine/services/updates.py`.
    - [ ] Sub-task: Write tests for parsing various GitHub API responses.
    - [ ] Sub-task: Implement robust error handling for network timeouts and 403 (Rate Limited).
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Logic & Polling
- [ ] Task: Implement `UpdateManager` (Polling, comparison logic).
    - [ ] Sub-task: Write `version_compare` tests (e.g., v0.1.5 vs 0.1.6).
    - [ ] Sub-task: Implement 24-hour background timer.
- [ ] Task: Integrate `UpdateManager` into `AppCoordinator` (startup trigger).
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: UI Integration
- [ ] Task: Modify `engine/ui.py` (TrayIcon) for dynamic menu labels.
    - [ ] Sub-task: Create Signal/Callback from UpdateManager to UI.
- [ ] Task: Implement 'Open Browser' action for the version label.
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase 4: Final Validation
- [ ] Task: End-to-end verify update flow with mock API responses.
- [ ] Task: Execute the project's "Definition of Done Gate":
    - [ ] Sub-task: `uv run ruff check .`
    - [ ] Sub-task: `uv run ruff format --check .`
    - [ ] Sub-task: `uv run mypy .`
    - [ ] Sub-task: `uv run pytest -q`
- [ ] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)
