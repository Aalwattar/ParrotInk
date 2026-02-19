"""
Centralized constants for the ParrotInk engine.
Follows First Principles by consolidating magic numbers and security invariants.
"""

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
