# Implementation Plan: Config Fidelity & Audio Privacy UX

## Phase 1: Configuration Fidelity (tomlkit) [checkpoint: b72854c]
- [x] Task: Add `tomlkit` to `pyproject.toml` dependencies and run `uv lock`. 9bfd6be
- [x] Task: Update `engine/config.py` to use `tomlkit` for reading and writing `config.toml`, ensuring comments and original document structure are preserved. 4b1df17
- [x] Task: Create or update unit tests in `tests/test_config.py` to verify that saving a config change does not strip comments. 4b1df17
- [x] Task: Conductor - User Manual Verification 'Configuration Fidelity' (Protocol in workflow.md) b72854c

## Phase 2: Dynamic Diagnostic & Pipeline Guard
- [ ] Task: Modify `main.py` `start_listening` to run the OS diagnostic *before* attempting any provider connection. If blocked, return early and do not enter `CONNECTING` state.
- [ ] Task: Ensure that mid-session hotkey presses with a blocked mic correctly trigger the error path and update the UI bridge immediately (preventing the need for an app restart).
- [ ] Task: Conductor - User Manual Verification 'Dynamic Diagnostic & Pipeline Guard' (Protocol in workflow.md)

## Phase 3: Enhanced Privacy UI & Popups
- [ ] Task: Update descriptive text strings in `main.py` and `engine/ui.py` to correctly reference "Privacy & security > Microphone" (Windows 11).
- [ ] Task: Implement a styled, interactive popup dialog (using `ttkbootstrap.dialogs` or `tkinter.messagebox`) in `engine/ui.py` that explains the microphone block and provides an "Open Settings" button.
- [ ] Task: Modify `engine/indicator_ui.py` and `engine/hud_renderer.py` to ensure that critical hardware error messages (like privacy blocks) do not automatically disappear after 1 second, but remain visible until the state changes or the user dismisses them.
- [ ] Task: Conductor - User Manual Verification 'Enhanced Privacy UI & Popups' (Protocol in workflow.md)
