# Implementation Plan: Unified Configuration & Interaction Overhaul

## Phase 1: Schema Refine & Validation [checkpoint: eb5fc92]
Goal: Simplify the TOML structure and implement high-level profiles.

- [x] Task: Update `engine/config.py` with the new schema. e3983db
  - [x] Sub-task: Implement `latency_profile` and `mic_profile` enums.
  - [x] Sub-task: Add Pydantic validation for `volume` (0..1) and `inactivity_timeout` (5..3600).
  - [x] Sub-task: Consolidate `language` and `sample_rate` to global keys.
- [x] Task: Implement mapping logic to derive engineering values from profiles. e3983db
- [x] Task: Update `migrate_config_file` to handle the new structure. e3983db
- [x] Task: Conductor - User Manual Verification 'Schema Refine & Validation' (Protocol in workflow.md)

## Phase 2: In-Flight Updates & Provider Alignment [checkpoint: 84737ae]
Goal: Implement smart updates and ensure strict API compliance.

- [x] Task: Add `update_and_save()` method to the `Config` class. 6db4b0f
- [x] Task: Refactor `OpenAIProvider` for Realtime Transcription alignment. 6db4b0f
  - [x] Sub-task: `session.type = "transcription"`, 24k rate, model separation.
- [x] Task: Refactor `AssemblyAIProvider` for V3 alignment. 6db4b0f
  - [x] Sub-task: Regional endpoints, remove legacy params.
- [x] Task: Update `AudioAdapter` to support resampling to 24k for OpenAI. 6db4b0f
- [x] Task: Conductor - User Manual Verification 'In-Flight Updates & Provider Alignment' (Protocol in workflow.md)

## Phase 3: Interactive Hotkey UI [checkpoint: fc0e7ab]
Goal: Implement the "Change Hotkey" flow.

- [x] Task: Create `engine/platform_win/hotkey_recorder.py` for Win32 key capture.
- [x] Task: Update `engine/ui.py` to add "Change Hotkey" tray menu item.
- [x] Task: Implement the recording flow:
  - [x] Sub-task: Show modal prompt.
  - [x] Sub-task: Capture and validate (reject Win+L, Alt+F4, etc.).
  - [x] Sub-task: Apply change via `Config.update_and_save()`.
- [x] Task: Update `AppCoordinator` to reload the listener on config change.
- [x] Task: Conductor - User Manual Verification 'Interactive Hotkey UI' (Protocol in workflow.md)

## Phase 4: Polishing & Final DOD
Goal: Address bug fixes, UX refinements, and quality gates.

- [ ] Task: Fix `app config --explain` CLI crash.
  - [ ] Sub-task: Wrap `load_config` in `main.py` to print a clean error instead of a stack trace for invalid TOML.
- [ ] Task: Refine Hotkey Validation & UX.
  - [ ] Sub-task: Update `HotkeyRecorder` to allow single keys (F1-F12, etc.) but block "Modifiers-Only."
  - [ ] Sub-task: Create HUD-styled `HotkeyRecordingWindow` in `engine/platform_win/hotkey_dialog.py`.
  - [ ] Sub-task: Implement live-update text in the recording dialog.
- [ ] Task: Fix HUD Click-Through.
  - [ ] Sub-task: Add `WS_EX_TRANSPARENT` style and set `WM_NCHITTEST` to `HTTRANSPARENT`.
- [ ] Task: Final Code Archaeology & Cleanup.
  - [ ] Sub-task: Remove any remaining dead code or legacy "bridge" variables.
- [ ] Task: Pass DOD Gate (Ruff, Mypy, Pytest).
- [ ] Task: Conductor - User Manual Verification 'Diagnostics & Final DOD' (Protocol in workflow.md)
