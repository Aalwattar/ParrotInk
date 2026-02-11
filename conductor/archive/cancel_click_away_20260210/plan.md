# Implementation Plan: Cancel Dictation on Click Outside Anchor

## Phase 1: Foundation & Mouse Monitoring
Initialize the mouse monitoring infrastructure and configuration.

- [x] Task: Update `engine/config.py` with new interaction settings.
    - [x] Add `cancel_on_click_outside_anchor` (bool, default true).
    - [x] Add `anchor_scope` (Literal["control", "window"], default "control").
- [x] Task: Create `engine/mouse.py` for global mouse hooks.
    - [x] Implement a `MouseMonitor` class using `pynput.mouse.Listener`.
    - [x] Add a callback for `on_click` to detect left-clicks.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Foundation & Mouse Monitoring' (Protocol in workflow.md)

## Phase 2: Anchor Capture & Comparison
Implement the logic to capture the anchor and compare it with click targets.

- [x] Task: Implement Anchor capturing in `AppCoordinator`.
    - [x] When dictation starts, capture the current foreground HWND or focused UI element based on `anchor_scope`.
    - [x] Use `pywin32` for window handles and a UI Automation library for control-level precision.
- [x] Task: Implement comparison logic.
    - [x] On left click, resolve the target under the cursor.
    - [x] Mismatch detection: if the target doesn't match the anchor, trigger cancellation.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Anchor Capture & Comparison' (Protocol in workflow.md)

## Phase 3: Integration & UX
Connect the mouse monitoring to the dictation lifecycle.

- [x] Task: Integrate `MouseMonitor` into `AppCoordinator`.
    - [x] Start monitoring when listening begins.
    - [x] Stop monitoring when listening ends.
- [x] Task: Ensure robust cleanup.
    - [x] Ensure the mouse hook is released even if the application crashes or the session is cancelled via hotkey.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Integration & UX' (Protocol in workflow.md)

## Phase 4: Final Validation
Verify the feature against all acceptance criteria.

- [x] Task: Run full suite of automated and manual tests.
    - [x] Verify `window` scope functionality.
    - [x] Verify `control` scope functionality.
    - [x] Verify passthrough for other mouse events.
- [x] Task: Conductor - User Manual Verification 'Phase 4: Final Validation' (Protocol in workflow.md)
