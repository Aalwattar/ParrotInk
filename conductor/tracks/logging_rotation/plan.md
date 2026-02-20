# Implementation Plan: Rotational Logging

## Phase 1: Configuration & Infrastructure
- [x] **Task:** Update `LoggingConfig` in `engine/config.py` with `max_bytes` and `backup_count`.
- [x] **Task:** Update `config.example.toml` with the new logging options.

## Phase 2: Logging Refactor
- [x] **Task:** Modify `engine/logging.py` to use `RotatingFileHandler`.
- [x] **Task:** Ensure `get_log_path` creates necessary directories.
- [x] **Task:** Implement sanitization and formatting consistency in the new handler.

## Phase 3: Validation
- [x] **Task:** Create `tests/test_logging_rotation.py` to verify:
  - File creation in the correct directory.
  - Rotation logic when file size exceeds limits.
  - Configuration adherence (enabling/disabling).
- [x] **Task:** Run full DoD Gate.
