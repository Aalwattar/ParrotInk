# Track Spec: Boringly Simple Stability (Consultant Approved)

## Objective
Implement the minimum necessary changes to guarantee Windows stability by enforcing Thread Ownership and Atomic I/O.

## Core Requirements
1. **Single-Owner Thread Rule**: ONLY the Asyncio Main Loop thread may mutate configuration or application state. Tray callbacks must hand off via `loop.call_soon_threadsafe`.
2. **Atomic Config Save**: Use `Temp file -> Flush -> Rename` to prevent `config.toml` corruption.
3. **Lean Hooks**: Keep existing `pynput` hooks but ensure callbacks are logic-free (queue hand-off only).
4. **Isolated Recording**: Capture hotkeys via local window messages, not global hooks.

## Rejected Changes (Over-reactions)
- DO NOT switch to the `keyboard` library.
- DO NOT implement persistent process-wide GDI+.
- DO NOT refactor the entire interaction layer.
