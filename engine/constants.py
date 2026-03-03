"""
Centralized constants for the ParrotInk engine.
Follows First Principles by consolidating magic numbers and security invariants.
"""

import os

# Environment: Check if running in a headless CI environment
IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"

# Security Invariants: Base trusted domains for transcription providers.
# These can be augmented via config.toml.
TRUSTED_DOMAINS = {
    "api.openai.com",
    "streaming.assemblyai.com",
    "streaming.eu.assemblyai.com",
    "localhost",
    "127.0.0.1",
}

# Privacy: Number of characters to keep unmasked in logs for context.
PII_REDACTION_LENGTH = 10

# Interaction Timing
COOLDOWN_MANUAL_STOP = 0.5  # Seconds to wait after starting before allowing key-stop
COOLDOWN_INJECTION = 0.5  # Seconds to ignore keys after our own injection
INTENT_LOCKOUT_DURATION = 0.3  # Seconds to ignore rapid toggle triggers
TOGGLE_DEBOUNCE_COOLDOWN = 0.4  # Seconds for native toggle suppression

# Watchdogs and Health
HOOK_WATCHDOG_INTERVAL = 30.0  # Seconds between dead-hook checks
SESSION_QUIT_TIMEOUT = 2.0  # Seconds to wait for thread join on quit

# UI Constants
DEFAULT_MAX_CHARS = 180

# URLs
URL_HOMEPAGE = "https://github.com/Aalwattar/ParrotInk"
URL_ISSUES = "https://github.com/Aalwattar/ParrotInk/issues"

# UI Status Messages (Unified)
STATUS_CONNECTING = "Connecting..."
STATUS_READY = "Ready"
STATUS_RETRYING = "Retrying..."
STATUS_FAILED = "Connection Failed"
STATUS_RELOADING = "Reloading..."
STATUS_CONFIG_UPDATED = "Config Updated"
STATUS_RELOAD_FAILED = "Reload Failed"
STATUS_LISTENING = "Listening..."
STATUS_FINALIZED = "Finalized"
