# Implementation Plan: Unified Configuration & Interaction Overhaul

## Phase 1: Schema Refine & Validation
Goal: Simplify the TOML structure and implement high-level profiles.

- [x] Task: Update `engine/config.py` with the new schema. e3983db
  - [x] Sub-task: Implement `latency_profile` and `mic_profile` enums.
  - [x] Sub-task: Add Pydantic validation for `volume` (0..1) and `inactivity_timeout` (5..3600).
  - [x] Sub-task: Consolidate `language` and `sample_rate` to global keys.
- [x] Task: Implement mapping logic to derive engineering values from profiles. e3983db
- [x] Task: Update `migrate_config_file` to handle the new structure. e3983db
- [ ] Task: Conductor - User Manual Verification 'Schema Refine & Validation' (Protocol in workflow.md)

## Phase 2: In-Flight Updates & Provider Alignment
Goal: Implement smart updates and ensure strict API compliance.

- [ ] Task: Add `update_and_save()` method to the `Config` class.
- [ ] Task: Refactor `OpenAIProvider` for Realtime Transcription alignment.
  - [ ] Sub-task: `session.type = "transcription"`, 24k rate, model separation.
- [ ] Task: Refactor `AssemblyAIProvider` for V3 alignment.
  - [ ] Sub-task: Regional endpoints, remove legacy params.
- [ ] Task: Conductor - User Manual Verification 'In-Flight Updates & Provider Alignment' (Protocol in workflow.md)

## Phase 3: Interactive Hotkey UI
Goal: Implement the "Change Hotkey" flow.

- [ ] Task: Create `engine/platform_win/hotkey_recorder.py` for Win32 key capture.
- [ ] Task: Update `engine/ui.py` to add "Change Hotkey" tray menu item.
- [ ] Task: Implement the recording flow:
  - [ ] Sub-task: Show modal prompt.
  - [ ] Sub-task: Capture and validate (reject Win+L, Alt+F4, etc.).
  - [ ] Sub-task: Apply change via `Config.update_and_save()`.
- [ ] Task: Update `InteractionMonitor` to reload the listener on config change.
- [ ] Task: Conductor - User Manual Verification 'Interactive Hotkey UI' (Protocol in workflow.md)

## Phase 4: Diagnostics & Final DOD
Goal: Finalize tools and quality gates.

- [ ] Task: Implement `app config --explain` with secrets redaction.
- [ ] Task: Verify startup "Fail Fast" UI notification for broken configs.
- [ ] Task: Pass DOD Gate (Ruff, Mypy, Pytest).
- [ ] Task: Conductor - User Manual Verification 'Diagnostics & Final DOD' (Protocol in workflow.md)
