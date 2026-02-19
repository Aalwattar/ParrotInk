# Security and Privacy Audit Report
**Date:** 2026-02-19
**Status:** Resolved

## Remediation Summary

### Finding 1: Sensitive Data Leak via User-Supplied WebSocket URL
*   **Status:** Fixed
*   **Remediation:** Implemented `SecurityManager.is_url_trusted()` to validate WebSocket URLs against an allow-list of known provider domains. Providers now refuse to connect and send API keys to untrusted endpoints unless in explicit test mode.

### Finding 2: Pydantic Validation Bypass in `_deep_merge`
*   **Status:** Fixed
*   **Remediation:** Removed the insecure `_deep_merge` method. Refactored `Config.update_and_save()` to merge updates into a temporary dictionary and perform a full `model_validate()` before applying changes to the live configuration.

### Finding 3: PII Leak in Logs
*   **Status:** Fixed
*   **Remediation:** Added `TRANSCRIPT_PATTERN` to `SanitizingFormatter` to automatically mask transcription content in logs. Lowered transcription result log levels from `INFO` to `DEBUG` and wrapped them in structured keys to ensure consistent redaction.

### Finding 4: Path Traversal in Log File Path
*   **Status:** Fixed
*   **Remediation:** Implemented `is_path_safe()` using `os.path.commonpath` to ensure log files are only written to allowed application and temporary directories. `configure_logging()` now falls back to the default safe path if an unsafe path is detected.
