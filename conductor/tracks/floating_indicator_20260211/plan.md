# Implementation Plan: Floating Acrylic Recording Indicator

## Phase 1: Foundation and Win32 Acrylic Window
Goal: Establish the base Win32 window in an isolated module with Acrylic transparency and draggability.

- [ ] Task: Create `tests/test_indicator_ui.py` with failing tests for window lifecycle and basic state.
- [ ] Task: Implement isolated Win32 window class in `engine/indicator_ui.py` using `ctypes`.
- [ ] Task: Implement "Acrylic" (Blur-behind) effect using `SetWindowCompositionAttribute` in `engine/indicator_ui.py`.
- [ ] Task: Implement draggability logic (handling `WM_NCHITTEST`) within the new module.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Foundation' (Protocol in workflow.md)

## Phase 2: State Visualization and Engine Integration
Goal: Connect the isolated indicator to the application state via UIBridge.

- [ ] Task: Add tests in `tests/test_indicator_ui.py` for status-based visual transitions.
- [ ] Task: Implement `update_status(is_recording: bool)` in `engine/indicator_ui.py` with smooth color transitions.
- [ ] Task: Update `engine/ui_bridge.py` to manage the lifecycle of the `IndicatorWindow`.
- [ ] Task: Connect `AppCoordinator` start/stop events to the indicator via the bridge.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: State Visualization' (Protocol in workflow.md)

## Phase 3: Side-car Panel and Partial Text Buffer
Goal: Implement the translucent side-car panel and the 3-5 word partial text buffer.

- [ ] Task: Add buffer logic tests (3-5 words sliding window) to `tests/test_indicator_ui.py`.
- [ ] Task: Implement the "side-car" text panel as a linked component within `engine/indicator_ui.py`.
- [ ] Task: Implement `update_partial_text(text: str)` with sliding window logic in the new module.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Side-car Panel' (Protocol in workflow.md)

## Phase 4: Final Polishing and Cleanup
Goal: Refine the Fluent aesthetic and perform final DOD Gate.

- [ ] Task: Refine Acrylic blur settings and opacity for optimal "Fluent" look.
- [ ] Task: Perform final DOD Gate (Ruff, Mypy, Pytest).
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Final Polishing' (Protocol in workflow.md)
