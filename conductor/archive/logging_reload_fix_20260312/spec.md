# Dynamic Logging Reload

## Objective
Ensure that changes to the `log_level` in the configuration file are applied dynamically across the application without requiring a full restart.

## Context
Currently, the Python `logging` module is initialized once at application startup. When the user modifies the `.toml` configuration and clicks "Reload Configuration", the `Config` object updates its internal state, but it does not broadcast this change to the logging system. Consequently, new logging thresholds (e.g., changing from ERROR to INFO or DEBUG) are ignored until the next application launch. The goal is to update the logging level at runtime without re-initializing file handles or drivers.

## Execution Plan

### Phase 1: Update Logging Service Interface
- **Action:** Add a `set_global_level(level: str)` function to `engine/logging.py`.
- **Action:** This function should iterate through all active loggers (or modify the root logger/handlers directly) and apply the new `logging.LEVEL` dynamically using standard `.setLevel()` calls.
- **Action:** Ensure this function safely translates string levels ("DEBUG", "INFO", "WARNING", "ERROR") to their corresponding `logging` constants.

### Phase 2: Configuration Observer Integration
- **Action:** In `main.py` (or the relevant central configuration observer like `AppCoordinator._on_config_changed`), add a hook that calls the new `set_global_level()` function whenever a configuration reload is detected.
- **Action:** Pass `config.transcription.log_level` (or the appropriate config path) to this function.

### Phase 3: Verification
- **Action:** Create a test to verify that calling `set_global_level()` successfully changes the threshold for existing loggers in memory.
- **Action:** Manually verify by starting the app in ERROR mode, changing the config to DEBUG, hitting Reload, and confirming that DEBUG messages immediately begin appearing in the `parrotink.log` file.
