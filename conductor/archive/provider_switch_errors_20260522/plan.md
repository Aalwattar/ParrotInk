# Implementation Plan: Provider Switching & Error Handling Fixes

## Phase 1: Fix Provider Switching & Restore Signal Routing
- [x] Task: Create a new branch (e.g., `fix/provider-switch-and-errors`) from `master` to isolate the work for this track. 83ae857
- [x] Task: Investigate signal routing for provider switching (tray menu & hotkeys) to identify the regression root cause. Document findings in plan. 7847ad3
    - Findings:
        1. `gui_main.py` is missing `on_provider_change`, `on_set_key`, and `on_toggle_sounds` callbacks in the `TrayApp` constructor call.
        2. Providers (`assemblyai_provider.py`, `openai_provider.py`) log errors but do not propagate them via callbacks to the UI.
        3. No structured error handling exists to transition HUD/Tray to an Error state.
- [x] Task: Create a reproduction test `tests/repro_tray_callbacks.py` that verifies `TrayApp` in `gui_main.py` is initialized with the required callbacks. 22f9cfc
- [x] Task: Implement the minimal fix in `engine/gui_main.py` by passing the missing callbacks to `TrayApp`. 22f9cfc
- [x] Task: Update `AppCoordinator._on_config_changed` in `main.py` to ensure that a provider change triggers an immediate and clean `stop_provider()` in `ConnectionManager` to close the old connection. 22f9cfc
- [x] Task: Verify the fix with the reproduction test and manual verification of logs during a tray-initiated switch. 22f9cfc
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Fix Provider Switching' (Protocol in workflow.md)

## Phase 2: Structured Error Handling & UI Feedback
- [x] Task: Define a unified `TranscriptionError` structure (e.g., in `engine/app_types.py`) with fields for `title` and `message`. 22f9cfc
- [x] Task: Update `BaseProvider` in `engine/transcription/base.py` to accept an `on_error` callback. 22f9cfc
- [x] Task: Update `TranscriptionFactory`, `ConnectionManager`, and `AppCoordinator` to propagate this `on_error` callback from the provider up to the coordinator. 22f9cfc
- [x] Task: Implement specific error mapping in `AssemblyAIProvider` (e.g., mapping "Insufficient funds" to a user-friendly message) and `OpenAIProvider`. 22f9cfc
- [x] Task: Update `AppCoordinator.set_state` and `UIBridge` to handle a transition to `AppState.ERROR`, ensuring the HUD turns red and displays the error title/message. 22f9cfc
- [x] Task: Write and run integration tests (e.g., `tests/test_error_flow.py`) simulating a provider error and verifying the HUD/Tray update. 22f9cfc
- [x] Task: Final project-wide verification: `uv run pytest`, `uv run ruff check`, `uv run mypy .`. 22f9cfc
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Error Handling' (Protocol in workflow.md)
