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

- [~] Task: Update `AssemblyAIProvider`
    - [ ] Ensure `on_partial` is called for EVERY `Turn` message regardless of `end_of_turn`.
    - [ ] Switch back to sending the **cumulative** transcript in `on_partial` so the Coordinator can diff it.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: AssemblyAI Immediate Partials' (Protocol in workflow.md)

## Phase 3: Interaction & Performance Fixes
Ensure Toggle mode stop is reliable and not blocked by logs.

- [ ] Task: Refine `AppCoordinator._on_manual_stop`
    - [ ] Improve logic to ensure *any* key (including modifiers) stops the session in Toggle mode.
    - [ ] Debug potential race conditions between hotkey release and interaction monitor.
- [ ] Task: Optimize Logging
    - [ ] Ensure `websockets` and `DEBUG` logging aren't saturated/blocking the main loop.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Interaction & Performance Fixes' (Protocol in workflow.md)
