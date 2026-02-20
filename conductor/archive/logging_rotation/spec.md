# Specification: Rotational Logging & AppData Storage

## 1. Goal
Implement a persistent, size-limited logging system that stores application logs in a standard Windows user directory (`%LOCALAPPDATA%`). This is critical for debugging the application since it typically runs without a console window.

## 2. Requirements

### 2.1 File Storage
- **Location:** Logs MUST be stored in `%LOCALAPPDATA%/ParrotInk/logs/app.log` by default.
- **Organization:** The directory structure should be created automatically if it doesn't exist.

### 2.2 Rotation (Unbounded Growth Prevention)
- **Mechanism:** Use `logging.handlers.RotatingFileHandler`.
- **Max File Size:** Default to 5 MB per file.
- **Backup Count:** Keep the last 5 log files (total max 30 MB).

### 2.3 Configuration
- **Settings:**
  - `logging.file_enabled`: Toggle file logging.
  - `logging.file_max_bytes`: Max size before rotation.
  - `logging.file_backup_count`: Number of historical logs to keep.
  - `logging.file_level`: Logging level (DEBUG=0, INFO=1, etc.).

### 2.4 Safety & Performance
- **Non-blocking:** Maintain the existing `QueueListener` architecture to ensure logging doesn't block the main UI or audio threads.
- **Encoding:** Always use UTF-8.
- **Path Safety:** Ensure the path is within valid user directories.

## 3. Implementation Details
- **`engine/config.py`**: Update `LoggingConfig` model.
- **`engine/logging.py`**: Replace `FileHandler` with `RotatingFileHandler` and integrate new config parameters.
- **`engine/platform_win/paths.py`**: Verify `get_log_path()` logic.
- **`main.py`**: Ensure logging is initialized early.
