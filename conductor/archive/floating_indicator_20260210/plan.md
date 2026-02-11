# Implementation Plan: Floating Recording Indicator

## Phase 1: Window Foundation
Set up the borderless, draggable Tkinter window and its lifecycle.

- [x] Task: Update `engine/config.py` with `ui.floating_indicator` schema.
    - [x] Add `enabled`, `opacity_idle`, `opacity_active`, `x`, and `y` fields.
- [x] Task: Create `engine/indicator_ui.py` for the Floating Window.
    - [x] Implement a `FloatingIndicator` class using `tkinter.Tk`.
    - [x] Configure `overrideredirect(True)` and `topmost` attributes.
    - [x] Implement "Click to Drag" logic (binding `<Button-1>` and `<B1-Motion>`).
- [x] Task: Integrate lifecycle into `main.py`.
    - [x] Launch the Tkinter loop in a dedicated thread or alongside the tray icon.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Window Foundation' (Protocol in workflow.md)

## Phase 2: Visuals & Animation
Implement the subtle look and the pulsing recording effect.

- [x] Task: Implement the Idle vs. Active visual states.
    - [x] Use a Canvas to draw the subtle circle/ring.
    - [x] Set window transparency using `attributes("-alpha", ...)` based on state.
- [x] Task: Implement the "Pulse" animation.
    - [x] Create a recurring `.after()` loop to vary the ring size or opacity during recording.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Visuals & Animation' (Protocol in workflow.md)

## Phase 3: State Integration & Persistence
Connect the indicator to the app state and ensure position persistence.

- [x] Task: Sync state changes.
    - [x] Update `FloatingIndicator` when `AppCoordinator` transitions between `IDLE` and `LISTENING`.
- [x] Task: Implement Position Persistence.
    - [x] On window move (drag release), update the internal config.
    - [x] Save the current X/Y to `config.toml` when the app shuts down.
- [x] Task: Conductor - User Manual Verification 'Phase 3: State Integration & Persistence' (Protocol in workflow.md)

## Phase 4: Final Validation
Verify the UX quality and acceptances.

- [x] Task: Perform manual smoke tests for "Always on Top" and "Transparency".
- [x] Task: Verify that the indicator is non-disruptive and remembers its location.
- [x] Task: Conductor - User Manual Verification 'Phase 4: Final Validation' (Protocol in workflow.md)
