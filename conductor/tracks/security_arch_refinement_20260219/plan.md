# Implementation Plan: Security Architecture & Concurrency Refinement

## Phase 1: Constants & Invariants
- [x] **Task:** Create `engine/constants.py` and migrate `TRUSTED_DOMAINS`. [e5361af]
- [x] **Task:** Wire `config.toml` to allow optional user-defined trusted endpoints. [a1aeec0]
- [x] **Task:** De-hardcode provider stop timeout from `base.py` and increase to 7.0s in `AudioConfig`. [0c18dd4]

## Phase 2: Engine API Cleanup
- [ ] **Task:** Refactor `AppCoordinator._on_config_changed` to handle "silent" transitions.
- [ ] **Task:** Remove `silent` parameter from `stop_listening` and update all callers.

## Phase 3: Logging & Privacy
- [ ] **Task:** Refactor `SanitizingFormatter` to process `LogRecord.extra`.
- [ ] **Task:** Update `OpenAIProvider` and `AssemblyAIProvider` to use structured logging for transcripts.

## Phase 4: Pydantic Optimization
- [ ] **Task:** Replace `merge_dict` with Pydantic-native update logic in `Config`.

## Phase 5: Concurrency & Stability Audit
- [ ] **Task:** Perform a manual trace of the `reload` and `provider_switch` paths to identify potential deadlocks.
- [ ] **Task:** Implement "Double-Stop Guard" in `ConnectionManager` to prevent rapid transition issues.
- [ ] **Task:** Run DoD Gate (ruff, mypy, pytest).
