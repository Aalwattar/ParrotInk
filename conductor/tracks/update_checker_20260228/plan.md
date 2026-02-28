# Implementation Plan: GitHub Update Checker

## Phase 1: API Foundation [checkpoint: 7f1e0ba]
- [x] Task: Research GitHub `/releases/latest` schema and confirm `X-RateLimit-*` headers. (0ca51c0)
- [x] Task: Implement `GitHubClient` in `engine/services/updates.py`. (0ca51c0)
    - [x] Sub-task: Handle 404/403 states gracefully as "no update info". (0ca51c0)
    - [x] Sub-task: Check `X-RateLimit-Remaining` to avoid hitting hard limits. (0ca51c0)
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md) (7f1e0ba)

## Phase 2: Logic & Polling [checkpoint: 5041507]
- [x] Task: Implement `UpdateManager` (Background Thread + Callback). (0ca51c0)
    - [x] Sub-task: Use `packaging.version` for robust tag comparison (RC/Post support). (0ca51c0)
    - [x] Sub-task: Ensure API calls and parsing never run on the main UI thread. (0ca51c0)
- [x] Task: Integrate `UpdateManager` into `AppCoordinator` (startup trigger). (0ca51c0)
    - [x] Sub-task: Implement the 24-hour background timer. (0ca51c0)
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md) (5041507)

## Phase 3: UI Integration [checkpoint: 6c3f012]
- [x] Task: Modify `engine/ui.py` (TrayIcon) to use a clickable menu item for the version label. (153b079)
- [x] Task: Implement 'Open Browser' action for the version label. (153b079)
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md) (6c3f012)

## Phase 4: Final Validation
- [ ] Task: End-to-end verify update flow with mock API responses.
- [ ] Task: Execute the project's "Definition of Done Gate":
    - [ ] Sub-task: `uv run ruff check .`
    - [ ] Sub-task: `uv run ruff format --check .`
    - [ ] Sub-task: `uv run mypy .`
    - [ ] Sub-task: `uv run pytest -q`
- [ ] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)
