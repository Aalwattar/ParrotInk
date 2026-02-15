# Implementation Plan: enhanced_status_feedback_20260215

This plan extends the current status architecture to support detailed feedback messages.

## Phase 1: Architectural Extension (Messaging)
- [x] Task: Extend `UIBridge` and `UIEvent`.
    - [x] Add `UPDATE_STATUS_MESSAGE` to `UIEvent` in `engine/ui_bridge.py`.
    - [x] Add `update_status_message(message: str)` method to `UIBridge`.
- [x] Task: Update `TrayApp` to handle status messages.
    - [x] Modify `_poll_bridge` in `engine/ui.py` to process `UPDATE_STATUS_MESSAGE`.
    - [x] Update `self.icon.title` (tooltip) with the received message.
    - [x] Forward the message to the HUD if it's active.
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Engine Instrumentation
- [x] Task: Instrument `ConnectionManager` with status messages.
    - [x] Add a `status_callback` or use the existing bridge to send messages during connection and retries.
    - [x] Update `ensure_connected` to send "Connecting to [Provider]..." and "Retry [X]/3..." messages.
- [x] Task: Refactor Provider Switching.
    - [x] Modify `on_provider_change` in `engine/gui_main.py`.
    - [x] Instead of `app.indicator.hide()`, send a "Switching..." status message and ensure the HUD remains visible.
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: HUD Visual Refinement
- [x] Task: Update `IndicatorWindow` to display arbitrary status text.
    - [x] Ensure `update_status_icon` (or a new method) correctly renders the full message string on the Skia/GDI surface.
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase 4: Final Validation and Done Gate
- [x] Task: Run full "Definition of Done Gate":
    - [x] `uv run ruff check .`
    - [x] `uv run ruff format --check .`
    - [x] `uv run mypy .`
    - [x] `uv run pytest -q`
- [x] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)
