# Implementation Plan: Short Path Hotkey Migration

This track simplifies the hotkey architecture and implements selective suppression using the `keyboard` library.

## Phase 1: Infrastructure & Cleanup
- [x] Task: Add `keyboard` library to dependencies. [checkpoint: d18c394]
- [x] Task: Strip `engine/interaction.py`. [checkpoint: 38024ab]
    - [x] Remove `queue.Queue`.
    - [x] Remove `_worker_loop` and `WorkerThread`.
    - [x] Refactor `InputMonitor` to use `keyboard` hooks instead of `pynput.Listener`.
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Architectural Integration
- [x] Task: Simplify `main.py` (`AppCoordinator`). [checkpoint: 38024ab]
- [x] Task: Implement dynamic hotkey switching. [checkpoint: 4390596]
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Validation & Tests
- [x] Task: Update unit tests. [checkpoint: 38024ab]
- [x] Task: Manual Leakage Verification. [checkpoint: 53a31d1]
- [x] Task: Run full "Definition of Done Gate". [checkpoint: 53a31d1]
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase: Review Fixes
- [x] Task: Apply review suggestions [checkpoint: 69a91bd]
