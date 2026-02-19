# Product Spec: Security Architecture & Concurrency Refinement

**Objective:** Mature the implementation of recent security and privacy fixes by aligning them with the application's core architectural principles and ensuring thread safety.

## 1. Core Improvements

### 1.1 Centralized Security Constants
- **Problem:** Trusted domains and PII redaction lengths are hardcoded in logic.
- **Goal:** Move `TRUSTED_DOMAINS` and `REDACTION_LENGTH` to a central `engine/constants.py`.
- **Flexibility:** Allow power users to augment the trusted domain list via `config.toml`.

### 1.2 Unified State Transition (The "Silent Stop")
- **Problem:** `AppCoordinator.stop_listening` has a `silent` flag used by the GUI to prevent sound during provider switching. This is a "leak" of UI concerns into the core engine.
- **Goal:** Remove the `silent` parameter. `AppCoordinator` should detect when a stop is part of a provider-switch transition and suppress feedback internally.

### 1.3 Robust PII Sanitization
- **Problem:** Redaction relies on brittle regex parsing of JSON-like strings in the log formatter.
- **Goal:** Utilize Python's `logging.LogRecord.extra` parameter. Pass sensitive data as metadata so the `SanitizingFormatter` can mask it reliably regardless of the message format.

### 1.4 Pydantic-Native Updates
- **Problem:** `Config.update_and_save` uses a manual dictionary merge logic.
- **Goal:** Fully utilize Pydantic's `model_validate` and standard update patterns to ensure 100% schema compliance and cleaner code.

## 2. Concurrency & Safety
- **Audit Requirement:** Systematically review the bridge between the GUI Thread, Hook Threads, and the Asyncio Loop.
- **Focus Areas:**
    - **Provider Switching:** Ensure no race conditions occur when `stop_provider` is called while a recording is being stopped or started.
    - **Config Reload:** Ensure the `_update_lock` in `Config` correctly protects against partial state visibility during observer notification.
