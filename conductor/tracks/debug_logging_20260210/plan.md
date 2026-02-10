# Implementation Plan: Verbose Debugging & Logging System

## Phase 1: Logging Infrastructure & Configuration [checkpoint: 512f4b2]
Establish the logging module, configuration schema, and non-blocking handler.

- [x] Task: Update Configuration Schema [512f4b2]
    - [x] Add `LoggingConfig` model to `engine/config.py` with `file_enabled`, `file_path`, and `file_level`.
    - [x] Integrate `LoggingConfig` into the main `Config` object.
    - [x] Update `config.example.toml` with the new `[logging]` section.
- [x] Task: Implement `engine/logging.py` [512f4b2]
    - [x] Create `SanitizingFormatter` class to redact keys and truncate audio data.
    - [x] Setup `configure_logging(config, verbose_count, quiet)` function.
    - [x] Implement `QueueHandler` and `QueueListener` setup for non-blocking I/O.
    - [x] Verify platform-specific default paths using `platformdirs`.
- [x] Task: Write Tests for Logging Logic [512f4b2]
    - [x] **Red:** Create `tests/test_logging.py` ensuring secrets are redacted and audio is truncated.
    - [x] **Green:** Implement the logic to pass these safety checks.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Logging Infrastructure & Configuration' (Protocol in workflow.md) [512f4b2]

## Phase 2: CLI Integration & State Logging [checkpoint: 512f4b2]
Connect the CLI flags and instrument the core engine with Level 1 logs.

- [x] Task: Update `main.py` CLI Arguments [512f4b2]
    - [x] Add `--verbose` / `-v` (action="count"), `--quiet`, and `--log-file`.
    - [x] Call `configure_logging` immediately after argument parsing.
- [x] Task: Instrument Core Components (Level 1) [512f4b2]
    - [x] Update `AppCoordinator` to log state transitions (Idle, Listening).
    - [x] Update `AudioStreamer` to log chunk size/duration metrics (debug level).
    - [x] Update `BaseProvider` to log connection/disconnection events.
- [x] Task: Verify Console Output [512f4b2]
    - [x] **Red:** Write a test simulating CLI args and capturing stdout/stderr.
    - [x] **Green:** Ensure `-v` produces expected output and `-q` silences it.
- [x] Task: Conductor - User Manual Verification 'Phase 2: CLI Integration & State Logging' (Protocol in workflow.md) [512f4b2]

## Phase 3: Provider Instrumentation (Level 2) [checkpoint: 512f4b2]
Implement detailed, sanitized logging for WebSocket traffic.

- [x] Task: Instrument `OpenAIProvider` [512f4b2]
    - [x] Log outgoing JSON messages (sanitized) at Level 2.
    - [x] Log incoming JSON messages at Level 2.
- [x] Task: Instrument `AssemblyAIProvider` [512f4b2]
    - [x] Log outgoing binary/JSON messages (sanitized) at Level 2.
    - [x] Log incoming events at Level 2.
- [x] Task: Integration Testing [512f4b2]
    - [x] **Red:** Test that running with `-vv` captures mock provider traffic without leaking secrets.
    - [x] **Green:** Refine `SanitizingFormatter` if any leaks are detected.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Provider Instrumentation (Level 2)' (Protocol in workflow.md) [512f4b2]