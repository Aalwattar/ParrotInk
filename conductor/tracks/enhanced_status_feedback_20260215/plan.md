# Implementation Plan: enhanced_status_feedback_20260215

This plan extends the current status architecture to support detailed feedback messages.

## Phase 1: Architectural Extension (Messaging)
- [ ] Task: Extend `UIBridge` and `UIEvent`.
    - [ ] Add `UPDATE_STATUS_MESSAGE` to `UIEvent` in `engine/ui_bridge.py`.
    - [ ] Add `update_status_message(message: str)` method to `UIBridge`.
- [ ] Task: Update `TrayApp` to handle status messages.
    - [ ] Modify `_poll_bridge` in `engine/ui.py` to process `UPDATE_STATUS_MESSAGE`.
    - [ ] Update `self.icon.title` (tooltip) with the received message.
    - [ ] Forward the message to the HUD if it's active.
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Engine Instrumentation
- [ ] Task: Instrument `ConnectionManager` with status messages.
    - [ ] Add a `status_callback` or use the existing bridge to send messages during connection and retries.
    - [ ] Update `ensure_connected` to send "Connecting to [Provider]..." and "Retry [X]/3..." messages.
- [ ] Task: Refactor Provider Switching.
    - [ ] Modify `on_provider_change` in `engine/gui_main.py`.
    - [ ] Instead of `app.indicator.hide()`, send a "Switching..." status message and ensure the HUD remains visible.
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: HUD Visual Refinement
- [ ] Task: Update `IndicatorWindow` to display arbitrary status text.
    - [ ] Ensure `update_status_icon` (or a new method) correctly renders the full message string on the Skia/GDI surface.
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase 4: Final Validation and Done Gate
- [ ] Task: Run full "Definition of Done Gate":
    - [ ] `uv run ruff check .`
    - [ ] `uv run ruff format --check .`
    - [ ] `uv run mypy .`
    - [ ] `uv run pytest -q`
- [ ] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)
