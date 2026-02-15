# Implementation Plan: fix_hotkey_connection_20260215

This plan addresses the hotkey misfire regression and the systemic connection latency issues by hardening the architecture and investigating the root cause.

## Phase 1: Hotkey Logic Repair
- [ ] Task: Audit and Fix `AppCoordinator.on_press`.
    - [ ] Review `main.py` for incorrect `issubset` logic.
    - [ ] Implement strict equality checking: `current_keys == target_hotkey`.
    - [ ] Ensure "Stop on Any Key" logic doesn't falsely trigger on modifier keys alone.
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Generalized Network Hardening
- [ ] Task: Promote Disconnect Timeout to `BaseProvider`.
    - [ ] Modify `engine/transcription/base.py` to wrap the `stop()` abstract method call in a timeout.
    - [ ] Remove the specific timeout code from `OpenAIProvider` (deduplication).
- [ ] Task: Implement Retry with Backoff in `ConnectionManager`.
    - [ ] Update `engine/connection.py` to retry `provider.start()` on `TimeoutError` or `ConnectionError`.
    - [ ] Configurable retry count (default 3) and backoff factor.
- [ ] Task: Update Configuration Defaults.
    - [ ] Increase `connection_timeout_seconds` to 20s in `engine/config.py`.
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Diagnostics & Feedback
- [ ] Task: Add Performance Logging.
    - [ ] Instrument `ConnectionManager` with detailed `logger.info` timing logs for connection lifecycles.
- [ ] Task: Verify UI Feedback.
    - [ ] Ensure `ui_bridge.set_state(AppState.CONNECTING)` is called *before* the first connection attempt and remains active during retries.
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase 4: Final Validation and Done Gate
- [ ] Task: Run full "Definition of Done Gate":
    - [ ] `uv run ruff check .`
    - [ ] `uv run ruff format --check .`
    - [ ] `uv run mypy .`
    - [ ] `uv run pytest -q`
- [ ] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)
