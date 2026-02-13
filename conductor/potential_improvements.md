# Potential Improvements & Future Architecture

This document tracks architectural suggestions and potential improvements that are currently **out of scope** or **low ROI** but may be valuable in the future.

## 1. Strict Event-Driven Coordinator (Event Bus)

**Status:** Defer / Optional
**Source:** Consultant Recommendation (2026-02-13)

### Current State
We currently use a **Thread-Safe Async Scheduling** pattern (`run_coroutine_threadsafe`) for inputs, and explicit Queues for Audio/UI. This is stable and race-free for normal usage.

### When to Implement
Refactoring to a strict `Event` object model + Single Event Loop is only recommended if we need:
1.  **Deterministic Replay:** Recording user input sequences (hotkey + mouse) to reproduce bugs exactly.
2.  **Unified Instrumentation:** A single choke point to measure system latency (Input -> Action).
3.  **Complex Throttling:** If we encounter issues with rapid-fire hotkey triggers causing task explosion.

### Implementation Strategy (Incremental)
If this becomes necessary, follow this low-risk path:

*   **Phase 1: Instrumentation Wrapper:** Wrap `run_coroutine_threadsafe` calls to log events and count pending tasks without changing logic.
*   **Phase 2: Hybrid Event Queue:** Introduce `Coordinator.dispatch(event)` for keyboard/mouse inputs only. Keep providers direct.
*   **Phase 3: Full Unification:** Route all provider callbacks and internal signals through the bus.

## 2. Advanced Anchor Matching (UIA)

**Status:** Defer / High Risk
**Source:** Consultant Recommendation (2026-02-13)

### Current State
We use standard Win32 `WindowFromPoint` logic (via `ctypes`). This works for 95% of applications.

### When to Implement
If users report consistent issues injecting text into complex applications (like Word, browser canvases, or electron apps) where the window handle doesn't match the specific text control.

### Implementation Strategy
Switching to UI Automation (UIA) or `IAccessible` requires significantly heavier libraries (`comtypes`) and increases startup time. Only do this if Win32 proves insufficient for a core user base.
