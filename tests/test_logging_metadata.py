import logging
import pytest
from engine.logging import SanitizingFormatter
from engine.constants import PII_REDACTION_LENGTH

def test_sanitizing_formatter_extra_metadata():
    """Verify that SanitizingFormatter redacts sensitive keys in LogRecord.extra."""
    formatter = SanitizingFormatter("%(message)s")
    
    # Case 1: Sensitive data in 'transcript' extra
    text = "This is my clinical note for Patient X."
    record = logging.LogRecord(
        name="test",
        level=logging.DEBUG,
        pathname="path",
        lineno=1,
        msg="Final segment",
        args=None,
        exc_info=None,
    )
    # Metadata is added to the __dict__ of the record by the logging system
    record.__dict__["transcript"] = text
    
    formatted = formatter.format(record)
    
    # ASSERT: The main message is intact
    assert "Final segment" in formatted
    
    # ASSERT: The extra metadata in the message string should be redacted
    # Note: Default Formatter doesn't include 'extra' in the message unless we tell it to.
    # But our SanitizingFormatter should look at the record itself.
    
    # Let's verify how we want this to work. First Principles:
    # If a developer uses logger.debug("msg", extra={"transcript": text}),
    # the transcript should NOT appear in the logs unmasked.
    
    # I will implement the formatter to APPEND redacted metadata if present.
    assert f"Metadata: transcript={text[:PII_REDACTION_LENGTH]}<PII_REDACTED>" in formatted
    assert "clinical note" not in formatted
