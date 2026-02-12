# Implementation Plan: Architecture & Design Cleanup (ROI-Focused)

Perform a holistic review and refactor of the `voice2text` codebase to improve isolation, organization, and separation of concerns while maintaining a high ROI.

## Phase 1: Discovery & Analysis (Initial Prerequisite)
Goal: Audit the codebase and produce a comprehensive refactoring proposal for user approval.

- [ ] Task: Audit `main.py`, `engine/coordinator.py` (if split), and `engine/ui_bridge.py` for leaked concerns.
- [ ] Task: Audit `engine/audio/` and `engine/transcription/` for contract purity and naming consistency.
- [ ] Task: Create `cleanup.md` report detailing identified "smells" and specific proposed refactors with ROI justification.
- [ ] Task: Conductor - User Manual Verification 'Cleanup Report Approval' (Protocol in workflow.md)

## Phase 2: Implementation Preparation
Goal: Establish a safe environment for the refactoring work.

- [ ] Task: Create a new git branch `refactor/architecture-cleanup`.
- [ ] Task: Conductor - User Manual Verification 'Branch Creation' (Protocol in workflow.md)

## Phase 3: Core & UI Decoupling
Goal: Sharpen the boundaries between the engine state and the user interface.

- [ ] Task: Refactor `AppCoordinator` to remove any direct awareness of UI implementation details.
- [ ] Task: Standardize `UIBridge` methods to ensure it acts as a true abstraction layer.
- [ ] Task: Write unit tests to verify that core coordination logic remains functional without UI modules.
- [ ] Task: Conductor - User Manual Verification 'Core & UI Decoupling' (Protocol in workflow.md)

## Phase 4: Provider & Audio Alignment
Goal: Ensure strict data contracts and consistent naming across the audio pipeline.

- [ ] Task: Align `BaseProvider` and its implementations with a unified error handling and state reporting pattern.
- [ ] Task: Refine `engine/audio/` utilities to ensure they focus strictly on data processing.
- [ ] Task: Verify naming consistency (e.g., `is_listening` vs `is_recording`) across all related modules.
- [ ] Task: Conductor - User Manual Verification 'Provider & Audio Alignment' (Protocol in workflow.md)

## Phase 5: Finalization & DOD Gate
Goal: Ensure the codebase is clean, consistent, and fully verified.

- [ ] Task: Perform a project-wide audit of unused imports, inconsistent comments, and variable naming.
- [ ] Task: Pass the final DOD Gate:
    - [ ] `uv run ruff check .`
    - [ ] `uv run ruff format .`
    - [ ] `uv run mypy .`
    - [ ] `uv run pytest -q`
- [ ] Task: Conductor - User Manual Verification 'Holistic Cleanup Finalization' (Protocol in workflow.md)
