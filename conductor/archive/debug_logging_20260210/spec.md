# Specification: Verbose Debugging & Logging System

## 1. Overview
This track introduces a robust, multi-level logging system to assist in debugging. It features CLI controls for console output, independent configuration for file logging, and strict security measures to redact sensitive data. All logging logic is encapsulated in a dedicated module to maintain code cleanliness.

## 2. Functional Requirements

### 2.1. CLI Interface
- **Flags:**
    - `--verbose` / `-v`: Increases console verbosity (Level 1).
    - `-vv`: Sets console verbosity to Level 2 (Detailed).
    - `--log-file <path>`: Overrides the configured log file path.
    - `--quiet` / `-q`: Suppresses all console output (overrides verbose flags).
- **Help:** Update `--help` to document these options.

### 2.2. Verbosity Levels
- **Level 1 (Basic):**
    - State transitions (Idle -> Connecting -> Listening).
    - Audio metrics (chunk size, duration).
    - Connection/Disconnection events.
- **Level 2 (Deep):**
    - Everything in Level 1.
    - Full JSON WebSocket messages (sanitized).

### 2.3. Output Format & Structure
- **Format:** Structured logging (e.g., `timestamp [LEVEL] [Provider] Event: {details}`).
- **Fields:** Must include timestamp, verbosity level, provider name, and event name.
- **Sanitization (CRITICAL):**
    - **Redact:** API Keys, Authorization headers, and credential identifiers.
    - **Truncate:** Raw audio payloads (base64/binary strings) must be replaced with placeholders (e.g., `<AUDIO_DATA_TRUNCATED>`).

### 2.4. Configuration (File Logging)
- Add a `[logging]` section to `config.toml`.
- **Options:**
    - `file_enabled` (bool): Enable persistent file logging (default: `false`).
    - `file_path` (string): Destination path. Default: Use `platformdirs.user_log_dir()` (e.g., `%LOCALAPPDATA%\ParrotInk\logs`).
    - `file_level` (int): Verbosity level for the file (1 or 2). Default: `1`.
- **Precedence:**
    - CLI flags control **console** verbosity only.
    - Config controls **file** logging independently.

### 2.5. Modular Architecture
- **Module:** Create `engine/logging.py`.
- **Implementation:** Use Python's standard `logging` library.
    - Use `QueueHandler` / `QueueListener` to ensure logging is **non-blocking** for the audio thread.
    - Implement custom formatters for redaction/truncation.

## 3. Non-Functional Requirements
- **Performance:** Logging must be asynchronous/non-blocking to prevent audio dropouts.
- **Security:** Zero-tolerance for logging secrets or full audio payloads.
- **Cleanliness:** Main application code should simple emit log events; formatting happens in the logger.

## 4. Acceptance Criteria
- Running with `-v` shows state/metrics; `-vv` shows sanitized JSON payloads.
- **Security Check:** Output (console & file) MUST NOT contain API keys or raw audio data.
- **Performance Check:** Application remains responsive and audio is glitch-free with `-vv`.
- File logging works independently of console flags (e.g., console quiet, file verbose).
- Default log file location follows platform standards.

## 5. Out of Scope
- Real-time UI log widget.
- Log rotation policies (start simple with append/overwrite).
