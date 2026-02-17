# Implementation Plan: Usage Statistics Tracking & Reporting

This plan outlines the steps for implementing persistent usage statistics tracking and a reporting dialog in ParrotInk.

## Phase 1: Data Model & Persistence
This phase focuses on creating the statistics storage mechanism and the logic to track metrics.

- [x] **Task: Define Statistics Schema and TDD Setup** [checkpoint: 924a0f4]
    - [x] Create `tests/test_stats.py` with failing tests for schema validation and default initialization.
    - [x] Define the `StatsModel` (Dataclass/TypedDict) and `StatsManager` class in a new `engine/stats.py` file.
- [x] **Task: Implement Persistent Storage (JSON)** [checkpoint: 924a0f4]
    - [x] Implement `StatsManager.load()` and `StatsManager.save()` using atomic writes to `%AppData%/ParrotInk/stats.json`.
    - [x] Verify tests pass for saving/loading across "restarts".
- [x] **Task: Implement Aggregation Logic (Daily/Monthly/Lifetime)** [checkpoint: 924a0f4]
    - [x] Write tests for date-based aggregation (Today vs This Month).
    - [x] Implement logic in `StatsManager` to handle timestamped session entries and roll up totals.
- [x] **Task: Conductor - User Manual Verification 'Phase 1: Data Model' (Protocol in workflow.md)** [checkpoint: 924a0f4]

## Phase 2: Integration with Audio Pipeline & App State
This phase integrates the tracker with the main application flow to collect data automatically.

- [x] **Task: Hook into AppCoordinator for Session End** [checkpoint: 924a0f4]
    - [x] Create `tests/test_stats_integration.py` to mock session completion.
    - [x] Update `AppCoordinator` in `main.py` to notify `StatsManager` when a transcription session finishes (incrementing counts, duration, and words).
- [x] **Task: Track Provider Usage and Errors** [checkpoint: 924a0f4]
    - [x] Add hooks to `AudioPipeline` or `AppCoordinator` to record which provider was used and if an error occurred.
    - [x] Verify that stats are updated correctly even on "Manual Stop" or "Click Away".
- [x] **Task: Conductor - User Manual Verification 'Phase 2: Integration' (Protocol in workflow.md)** [checkpoint: 924a0f4]

## Phase 3: UI Reporting (Tray & Dialog)
This phase adds the user-facing "Statistics" menu and the report dialog.

- [x] **Task: Implement Statistics Dialog (Tkinter)** [checkpoint: 924a0f4]
    - [x] Create a lightweight `Tkinter` dialog in `engine/ui_utils.py` or a new `engine/stats_ui.py`.
    - [x] Design the layout for Daily, Monthly, and Lifetime tables.
- [x] **Task: Update Tray Menu** [checkpoint: 924a0f4]
    - [x] Add "Statistics" menu item to `TrayApp` in `engine/ui.py`.
    - [x] Connect the menu item to trigger the `StatsManager` to fetch data and open the dialog.
- [x] **Task: Conductor - User Manual Verification 'Phase 3: UI Reporting' (Protocol in workflow.md)** [checkpoint: 924a0f4]

## Phase 4: Finalization & Polish
- [x] **Task: Final Verification and DOD Gate** [checkpoint: 924a0f4]
    - [x] Run `ruff`, `mypy`, and full `pytest` suite.
    - [x] Perform manual end-to-end test: Transcribe -> Check Stats -> Restart -> Check Stats.
- [ ] **Task: Conductor - User Manual Verification 'Phase 4: Finalization' (Protocol in workflow.md)**
