# Implementation Plan: fix_hotkey_connection_20260215

This plan addresses the hotkey misfire regression and the systemic connection latency issues by hardening the architecture and investigating the root cause.

## Phase 1: Hotkey Logic Repair
- [x] Task: Audit and Fix `AppCoordinator.on_press`.
    - [x] Review `main.py` for incorrect `issubset` logic.
    - [x] Implement strict equality checking: `current_keys == target_hotkey`.
    - [x] Ensure "Stop on Any Key" logic doesn't falsely trigger on modifier keys alone.
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Generalized Network Hardening
- [x] Task: Promote Disconnect Timeout to `BaseProvider`.
    - [x] Modify `engine/transcription/base.py` to wrap the `stop()` abstract method call in a timeout.
    - [x] Remove the specific timeout code from `OpenAIProvider` (deduplication).
- [x] Task: Implement Retry with Backoff in `ConnectionManager`.
    - [x] Update `engine/connection.py` to retry `provider.start()` on `TimeoutError` or `ConnectionError`.
    - [x] Configurable retry count (default 3) and backoff factor.
- [x] Task: Update Configuration Defaults.
    - [x] Increase `connection_timeout_seconds` to 20s in `engine/config.py`.
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Diagnostics & Feedback
- [x] Task: Add Performance Logging.
    - [x] Instrument `ConnectionManager` with detailed `logger.info` timing logs for connection lifecycles.
- [x] Task: Verify UI Feedback.
    - [x] Ensure `ui_bridge.set_state(AppState.CONNECTING)` is called *before* the first connection attempt and remains active during retries.
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase 4: Final Validation and Done Gate
- [x] Task: Run full "Definition of Done Gate":
    - [x] `uv run ruff check .`
    - [x] `uv run ruff format --check .`
    - [x] `uv run mypy .`
    - [x] `uv run pytest -q`
- [x] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)
