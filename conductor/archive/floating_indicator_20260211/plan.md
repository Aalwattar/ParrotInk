# Implementation Plan: Floating Acrylic Recording Indicator (Implemented as Luxury HUD)

## Phase 1: Foundation and Win32 Acrylic Window [checkpoint: d6343d3]
- [x] Task: Create `tests/test_indicator_ui.py` [d6343d3]
- [x] Task: Implement isolated Win32 window class in `engine/indicator_ui.py` [d6343d3]
- [x] Task: Implement "Acrylic" (Blur-behind) effect [d6343d3]
- [x] Task: Implement draggability logic [d6343d3]
- [x] Task: Conductor - User Manual Verification 'Phase 1: Foundation' [8884bdc]

## Phase 2: State Visualization and Engine Integration [checkpoint: 8884bdc]
- [x] Task: Add tests in `tests/test_indicator_ui.py` [8884bdc]
- [x] Task: Implement `update_status(is_recording: bool)` [8884bdc]
- [x] Task: Update `engine/ui_bridge.py` [8884bdc]
- [x] Task: Connect `AppCoordinator` start/stop events [8884bdc]
- [x] Task: Conductor - User Manual Verification 'Phase 2: State Visualization' [8884bdc]

## Phase 3: Side-car Panel and Partial Text Buffer [checkpoint: 8884bdc]
- [x] Task: Add buffer logic tests [8884bdc]
- [x] Task: Implement the "side-car" text panel [8884bdc]
- [x] Task: Implement `update_partial_text(text: str)` [8884bdc]
- [x] Task: Conductor - User Manual Verification 'Phase 3: Side-car Panel' [8884bdc]

## Phase 4: Final Polishing and Cleanup [checkpoint: 8884bdc]
- [x] Task: Refine Acrylic blur settings and opacity [8884bdc]
- [x] Task: Perform final DOD Gate (Ruff, Mypy, Pytest) [8884bdc]
- [x] Task: Conductor - User Manual Verification 'Phase 4: Final Polishing' [8884bdc]
