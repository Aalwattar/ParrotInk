# Implementation Plan: Real-Time AssemblyAI & Smart Interaction Fix

## Phase 1: Smart Overwrite Logic [checkpoint: 5fa4c90]
Implement the logic to handle partial corrections via backspacing.

- [x] Task: Update `engine/injector.py` [5fa4c90]
- [x] Task: Update `AppCoordinator` in `main.py` [0801f42]
- [x] Task: Conductor - User Manual Verification 'Phase 1: Smart Overwrite Logic' (Protocol in workflow.md) [8884bdc]

## Phase 2: AssemblyAI Immediate Partials [checkpoint: 97cb501]
Restore real-time streaming for AssemblyAI V3.

- [x] Task: Update `AssemblyAIProvider` [97cb501]
- [x] Task: Conductor - User Manual Verification 'Phase 2: AssemblyAI Immediate Partials' (Protocol in workflow.md) [8884bdc]

## Phase 3: Interaction & Performance Fixes [checkpoint: cb51c97]
Ensure Toggle mode stop is reliable and not blocked by logs.

- [x] Task: Refine `AppCoordinator._on_manual_stop` [cb51c97]
- [x] Task: Optimize Logging [cb51c97]
- [x] Task: Conductor - User Manual Verification 'Phase 3: Interaction & Performance Fixes' (Protocol in workflow.md) [8884bdc]
