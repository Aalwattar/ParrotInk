# Implementation Plan: Usage Statistics Tracking & Reporting

This plan outlines the steps for implementing persistent usage statistics tracking and a reporting dialog in ParrotInk.

## Phase 1: Data Model & Persistence
This phase focuses on creating the statistics storage mechanism and the logic to track metrics.

- [ ] **Task: Define Statistics Schema and TDD Setup**
    - [ ] Create `tests/test_stats.py` with failing tests for schema validation and default initialization.
    - [ ] Define the `StatsModel` (Dataclass/TypedDict) and `StatsManager` class in a new `engine/stats.py` file.
- [ ] **Task: Implement Persistent Storage (JSON)**
    - [ ] Implement `StatsManager.load()` and `StatsManager.save()` using atomic writes to `%AppData%/ParrotInk/stats.json`.
    - [ ] Verify tests pass for saving/loading across "restarts".
- [ ] **Task: Implement Aggregation Logic (Daily/Monthly/Lifetime)**
    - [ ] Write tests for date-based aggregation (Today vs This Month).
    - [ ] Implement logic in `StatsManager` to handle timestamped session entries and roll up totals.
- [ ] **Task: Conductor - User Manual Verification 'Phase 1: Data Model' (Protocol in workflow.md)**

## Phase 2: Integration with Audio Pipeline & App State
This phase integrates the tracker with the main application flow to collect data automatically.

- [ ] **Task: Hook into AppCoordinator for Session End**
    - [ ] Create `tests/test_stats_integration.py` to mock session completion.
    - [ ] Update `AppCoordinator` in `main.py` to notify `StatsManager` when a transcription session finishes (incrementing counts, duration, and words).
- [ ] **Task: Track Provider Usage and Errors**
    - [ ] Add hooks to `AudioPipeline` or `AppCoordinator` to record which provider was used and if an error occurred.
    - [ ] Verify that stats are updated correctly even on "Manual Stop" or "Click Away".
- [ ] **Task: Conductor - User Manual Verification 'Phase 2: Integration' (Protocol in workflow.md)**

## Phase 3: UI Reporting (Tray & Dialog)
This phase adds the user-facing "Statistics" menu and the report dialog.

- [ ] **Task: Implement Statistics Dialog (Tkinter)**
    - [ ] Create a lightweight `Tkinter` dialog in `engine/ui_utils.py` or a new `engine/stats_ui.py`.
    - [ ] Design the layout for Daily, Monthly, and Lifetime tables.
- [ ] **Task: Update Tray Menu**
    - [ ] Add "Statistics" menu item to `TrayApp` in `engine/ui.py`.
    - [ ] Connect the menu item to trigger the `StatsManager` to fetch data and open the dialog.
- [ ] **Task: Conductor - User Manual Verification 'Phase 3: UI Reporting' (Protocol in workflow.md)**

## Phase 4: Finalization & Polish
- [ ] **Task: Final Verification and DOD Gate**
    - [ ] Run `ruff`, `mypy`, and full `pytest` suite.
    - [ ] Perform manual end-to-end test: Transcribe -> Check Stats -> Restart -> Check Stats.
- [ ] **Task: Conductor - User Manual Verification 'Phase 4: Finalization' (Protocol in workflow.md)**
