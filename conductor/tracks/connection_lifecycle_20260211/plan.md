# Implementation Plan: Connection Lifecycle & Warm Connections (Track 4)

## Phase 1: Configuration & Connection Logic
Implement configuration and `ensure_connected`.

- [x] Task: Update Configuration Schema (Red Phase)
    - [x] Update `engine/config.py` and `config.example.toml`.
- [x] Task: Implement `ensure_connected` logic (Red Phase)
    - [x] Create tests in `tests/test_connection_lifecycle.py`.
    - [x] Implement `ensure_connected()` in `AppCoordinator`.
- [x] Task: Integrate `ensure_connected` with `start_listening` (Green Phase)
- [x] Task: Conductor - User Manual Verification 'Connection Logic' (Protocol in workflow.md)

## Phase 2: Warm Connection & Idle Timer
Implement monotonic idle timer.

- [x] Task: Implement Warm Idle Timer (Red Phase)
    - [x] Use monotonic timestamps + delayed check task.
    - [x] Verify `start_listening()` effectively "resets" activity.
- [x] Task: Implement Timer Expiry & Shutdown (Green Phase)
    - [x] Implement closure and `INFO` logging.
- [x] Task: Enforce Audio Invariant
    - [x] Guard `send_audio` to only allow when `state == LISTENING`.
- [x] Task: Conductor - User Manual Verification 'Warm Connection & Idle Timer' (Protocol in workflow.md)

## Phase 3: Session Rotation & Reconnection Strategy
Implement OpenAI rotation guard and backoff.

- [x] Task: Implement OpenAI Session Rotation & Guard (Red Phase)
    - [x] Create tests in `tests/test_openai_rotation.py`.
    - [x] Implement `rotation_pending` logic to avoid cutting off `LISTENING`.
- [x] Task: Implement Reconnection with Backoff (Green Phase)
- [x] Task: Final "Done" Gate Verification
    - [x] Run `uv run ruff check .`
    - [x] Run `uv run ruff format --check .`
    - [x] Run `uv run mypy .`
    - [x] Run `uv run pytest -q`
- [x] Task: Conductor - User Manual Verification 'Rotation & Reconnection' (Protocol in workflow.md)
