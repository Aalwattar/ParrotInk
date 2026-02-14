# Implementation Plan: Architecture & Design Cleanup (ROI-Focused)

Perform a holistic review and refactor of the `voice2text` codebase to improve isolation, organization, and separation of concerns while maintaining a high ROI.

## Phase 1: Discovery & Analysis (Initial Prerequisite)
Goal: Audit the codebase and produce a comprehensive refactoring proposal for user approval.

- [x] Task: Audit `main.py`, `engine/coordinator.py` (if split), and `engine/ui_bridge.py` for leaked concerns.
- [x] Task: Audit `engine/audio/` and `engine/transcription/` for contract purity and naming consistency.
- [x] Task: Create `cleanup.md` report detailing identified "smells" and specific proposed refactors with ROI justification.
- [x] Task: Conductor - User Manual Verification 'Cleanup Report Approval' (Protocol in workflow.md)

## Phase 2: Implementation Preparation
Goal: Establish a safe environment for the refactoring work.

- [x] Task: Create a new git branch `refactor/architecture-cleanup`.
- [x] Task: Conductor - User Manual Verification 'Branch Creation' (Protocol in workflow.md)

## Phase 3: Core & UI Decoupling
Goal: Sharpen the boundaries between the engine state and the user interface.

- [x] Task: Refactor `AppCoordinator` to remove any direct awareness of UI implementation details.
- [x] Task: Standardize `UIBridge` methods to ensure it acts as a true abstraction layer.
- [x] Task: Write unit tests to verify that core coordination logic remains functional without UI modules.
- [x] Task: Conductor - User Manual Verification 'Core & UI Decoupling' (Protocol in workflow.md)

## Phase 4: Provider & Audio Alignment
Goal: Ensure strict data contracts and consistent naming across the audio pipeline.

- [x] Task: Align `BaseProvider` and its implementations with a unified error handling and state reporting pattern.
- [x] Task: Refine `engine/audio/` utilities to ensure they focus strictly on data processing.
- [x] Task: Verify naming consistency (e.g., `is_listening` vs `is_recording`) across all related modules.
- [x] Task: Conductor - User Manual Verification 'Provider & Audio Alignment' (Protocol in workflow.md)

## Phase 5: Finalization & DOD Gate
Goal: Ensure the codebase is clean, consistent, and fully verified.

- [x] Task: Perform a project-wide audit of unused imports, inconsistent comments, and variable naming.
- [x] Task: Pass the final DOD Gate:
    - [x] `uv run ruff check .`
    - [x] `uv run ruff format .`
    - [x] `uv run mypy .`
    - [x] `uv run pytest -q`
- [x] Task: Conductor - User Manual Verification 'Holistic Cleanup Finalization' (Protocol in workflow.md)
