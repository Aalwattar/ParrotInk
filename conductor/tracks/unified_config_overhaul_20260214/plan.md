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

## Phase 4: Polishing & Final DOD [checkpoint: 6596dd1]
Goal: Address bug fixes, UX refinements, and quality gates.

- [x] Task: Fix `app config --explain` CLI crash. 6596dd1
  - [x] Sub-task: Wrap `load_config` in `main.py` to print a clean error instead of a stack trace for invalid TOML.
- [x] Task: Refine Hotkey Validation & UX. 6596dd1
  - [x] Sub-task: Update `HotkeyRecorder` to allow single keys (F1-F12, etc.) but block "Modifiers-Only."
  - [x] Sub-task: Create HUD-styled `HotkeyRecordingWindow` in `engine/platform_win/hotkey_dialog.py`.
  - [x] Sub-task: Implement live-update text in the recording dialog.
- [x] Task: Fix HUD Click-Through. 6596dd1
  - [x] Sub-task: Add `WS_EX_TRANSPARENT` style and set `WM_NCHITTEST` to `HTTRANSPARENT`.
- [x] Task: HUD Enhancements (User Requests). 6596dd1
  - [x] Sub-task: Add `click_through: bool = True` to `FloatingIndicatorConfig` and set `enabled = true` by default.
  - [x] Sub-task: Implement tray menu toggle for "Enable/Disable HUD".
  - [x] Sub-task: Make HUD click-through toggleable based on configuration.
- [x] Task: Final Code Archaeology & Cleanup. 6596dd1
  - [x] Sub-task: Remove any remaining dead code or legacy "bridge" variables.
- [x] Task: Pass DOD Gate (Ruff, Mypy, Pytest). 6596dd1
- [ ] Task: Conductor - User Manual Verification 'Diagnostics & Final DOD' (Protocol in workflow.md)

## Phase: Review Fixes
- [x] Task: Apply review suggestions 7a021c4
