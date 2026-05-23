# Implementation Plan: Provider Switching & Error Handling Fixes

## Phase 1: Analysis & Fix of Provider Switching Regression
- [ ] Task: Create a new branch (e.g., `fix/provider-switch-and-errors`) from `master` to isolate the work for this track.
- [ ] Task: Investigate signal routing for provider switching (tray menu & hotkeys) to identify the regression root cause. Document findings in plan.
- [ ] Task: Write failing test(s) that simulate provider switching and expect the new "lazy connect" behavior to be initialized and ready for a hotkey press.
- [ ] Task: Implement the minimal code changes necessary to fix the provider switching signal routing and enforce lazy connection.
- [ ] Task: Run full test suite, linting, and type checking (`uv run pytest`, `uv run ruff`, `uv run mypy`) to ensure no side effects.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Analysis & Fix of Provider Switching Regression' (Protocol in workflow.md)

## Phase 2: Structured Error Handling Implementation
- [ ] Task: Review AssemblyAI and OpenAI API documentation. Create a unified, structured error mapping (e.g., specific classes or enums for `insufficient_funds`, `unauthorized`, `rate_limit`).
- [ ] Task: Write failing test(s) that simulate critical errors from both providers and expect the system to emit a structured error event without crashing.
- [ ] Task: Implement the structured error catching and event emission mechanism in the provider interaction layer.
- [ ] Task: Write failing test(s) for the UI components (HUD & Tray Icon) expecting them to transition to an "Error" state visually upon receiving an error event.
- [ ] Task: Implement updates to the HUD and Tray Icon managers to correctly reflect and display specific error states.
- [ ] Task: Run full test suite, linting, and type checking (`uv run pytest`, `uv run ruff`, `uv run mypy`) to ensure all changes meet project standards.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Structured Error Handling Implementation' (Protocol in workflow.md)
