# Implementation Plan: Real-Time AssemblyAI & Smart Interaction Fix

## Phase 1: Smart Overwrite Logic
Implement the logic to handle partial corrections via backspacing.

- [x] Task: Update `engine/injector.py` [5fa4c90]
    - [x] Add `inject_backspaces(count: int)` function using `SendInput`. [5fa4c90]
- [x] Task: Update `AppCoordinator` in `main.py` [0801f42]
    - [x] Implement `_smart_inject(text: str)` that calculates common prefix vs. needed backspaces. [0801f42]
    - [x] Connect `on_partial` to `_smart_inject`. [0801f42]
    - [x] Ensure `on_final` performs a final sync and resets tracking. [0801f42]
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Smart Overwrite Logic' (Protocol in workflow.md)

## Phase 2: AssemblyAI Immediate Partials
Restore real-time streaming for AssemblyAI V3.

- [x] Task: Update `AssemblyAIProvider` [97cb501]
    - [x] Ensure `on_partial` is called for EVERY `Turn` message regardless of `end_of_turn`. [97cb501]
    - [x] Switch back to sending the **cumulative** transcript in `on_partial` so the Coordinator can diff it. [97cb501]
- [ ] Task: Conductor - User Manual Verification 'Phase 2: AssemblyAI Immediate Partials' (Protocol in workflow.md)

## Phase 3: Interaction & Performance Fixes
Ensure Toggle mode stop is reliable and not blocked by logs.

- [x] Task: Refine `AppCoordinator._on_manual_stop` [cb51c97]
    - [x] Improve logic to ensure *any* key (including modifiers) stops the session in Toggle mode. [cb51c97]
    - [x] Debug potential race conditions between hotkey release and interaction monitor. [cb51c97]
- [x] Task: Optimize Logging [cb51c97]
    - [x] Ensure `websockets` and `DEBUG` logging aren't saturated/blocking the main loop. [cb51c97]
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Interaction & Performance Fixes' (Protocol in workflow.md)
