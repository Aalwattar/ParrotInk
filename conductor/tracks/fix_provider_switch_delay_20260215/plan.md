# Implementation Plan: fix_provider_switch_delay_and_stutter

This plan addresses the 20-second delay, audio stuttering, and HUD persistence when switching providers. As a senior architect, the priority is to identify the threading or lifecycle mismanagement causing the block and ensure a debt-free resolution.

## Phase 1: Deep Architectural Investigation & Root Cause Analysis
- [ ] Task: Audit the `Connection` and `Interaction` lifecycle threading model.
    - [ ] Trace the `gui_main.py` -> `config_resolver` -> `provider_switch` event chain.
    - [ ] Identify where the 20s block occurs: is it a synchronous `.close()` call on a websocket in the UI thread?
- [ ] Task: Reproduce and log thread-id activity during the "stuttering" phase.
    - [ ] Create `tests/repro_switch_delay.py` to capture which threads are issuing stop signals and which thread is blocked.
- [ ] Task: **Architectural Review:** Present the root cause findings to the user.
    - [ ] Discuss if the issue is a blocking call in the main loop or a race condition in the audio pipeline cleanup.
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Refactor Disconnection & Lifecycle Management
- [ ] Task: Implement a robust, non-blocking disconnection protocol.
    - [ ] Ensure `Provider.disconnect()` is truly asynchronous and doesn't leak tasks.
    - [ ] Write unit tests in `tests/test_connection_lifecycle.py` to verify no "dangling" connections block the app during switch.
- [ ] Task: Refactor `InteractionCoordinator` to handle "Interrupted" states.
    - [ ] Ensure that a provider switch triggers a `FORCE_CANCEL` signal that bypasses standard "stop" sounds and logic.
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: UI/HUD State Synchronization
- [ ] Task: Decouple HUD visibility from provider disconnection.
    - [ ] Ensure the UI thread hides the HUD immediately upon the tray click, even if the backend cleanup is still in progress.
- [ ] Task: Gating Audio Feedback.
    - [ ] Implement a state-lock in `AudioFeedback` to prevent sound triggers during the transitional "Switching" state.
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase 4: Hotkey & Threading Integrity
- [ ] Task: Verify hotkey listener isolation.
    - [ ] Ensure the hotkey thread is never blocked by network I/O or provider teardown.
- [ ] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)

## Phase 5: Final Validation and Done Gate
- [ ] Task: Verify switch latency is under 2 seconds.
- [ ] Task: Run full "Definition of Done Gate":
    - [ ] `uv run ruff check .`
    - [ ] `uv run ruff format --check .`
    - [ ] `uv run mypy .`
    - [ ] `uv run pytest -q`
- [ ] Task: Conductor - User Manual Verification 'Phase 5' (Protocol in workflow.md)
