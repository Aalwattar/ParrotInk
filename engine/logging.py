import logging
import logging.handlers
import queue
import re
from pathlib import Path
from typing import List, Optional

from .platform_win.paths import get_log_path
from .constants import PII_REDACTION_LENGTH

# Regex for redacting sensitive information
# Redacts things like: authorization: Bearer sk-..., "api_key": "...", etc.
REDACT_PATTERNS = [
    (re.compile(r'(authorization":\s*"Bearer\s+)[^"]+'), r"\1<REDACTED>"),
    (re.compile(r'(api_key":\s*")[^"]+'), r"\1<REDACTED>"),
    (re.compile(r'("Authorization":\s*")[^"]+'), r"\1<REDACTED>"),
]

# Regex for truncating large audio data blocks
AUDIO_PATTERN = re.compile(r'("audio":\s*")[^"]{100,}')
AUDIO_DATA_PATTERN = re.compile(r'("audio_data":\s*")[^"]{100,}')

# Regex for redacting transcription results (PII protection)
# We mask the bulk of the transcript while keeping the first few chars for debugging context.
TRANSCRIPT_PATTERN = re.compile(
    rf'("(?:transcript|text)":\s*")([^"]{{0,{PII_REDACTION_LENGTH}}})[^"]+'
)


class SanitizingFormatter(logging.Formatter):
    """Formatter that redacts secrets and truncates audio data."""

    def format(self, record):
        msg = super().format(record)

        # Redact secrets
        for pattern, replacement in REDACT_PATTERNS:
            msg = pattern.sub(replacement, msg)

        # Truncate audio data
        msg = AUDIO_PATTERN.sub(r"\1<AUDIO_DATA_TRUNCATED>", msg)
        msg = AUDIO_DATA_PATTERN.sub(r"\1<AUDIO_DATA_TRUNCATED>", msg)

        # Mask transcription PII
        msg = TRANSCRIPT_PATTERN.sub(r"\1\2<PII_REDACTED>", msg)

        return msg


def is_path_safe(path: str | Path) -> bool:
    """
    Validates if a file path is safe for writing logs.
    Prevents path traversal and writing to sensitive system directories.
    """
    try:
        import os

        p = os.path.abspath(path)

        # Define allowed root directories (standard on Windows)
        allowed_roots = [
            os.path.abspath(os.environ.get("LOCALAPPDATA", "")),
            os.path.abspath(os.environ.get("APPDATA", "")),
            os.path.abspath(os.getcwd()),
            os.path.abspath(os.environ.get("TEMP", "")),
        ]

        # Senior Security Strategy: Use commonpath to verify p is within an allowed root.
        # We use .lower() for case-insensitive comparison on Windows.
        for root in allowed_roots:
            try:
                if os.path.commonpath([p, root]).lower() == root.lower():
                    return True
            except (ValueError, AttributeError):
                continue

        return False
    except Exception:
        return False


def get_default_log_path() -> Path:
    """Get the default platform-specific log file path."""
    log_path = Path(get_log_path())
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path


# Global listener to keep it alive
_listener: Optional[logging.handlers.QueueListener] = None


def configure_logging(config, verbose_count: int = 0, quiet: bool = False):
    """
    Sets up non-blocking logging to console and/or file.
    verbose_count: 0 (none), 1 (-v), 2+ (-vv)
    """
    global _listener

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Catch everything at root

    # Silence noisy loggers
    logging.getLogger("websockets").setLevel(logging.INFO)

    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    log_queue: queue.Queue = queue.Queue(-1)
    queue_handler = logging.handlers.QueueHandler(log_queue)
    logger.addHandler(queue_handler)

    handlers: List[logging.Handler] = []

    # 1. Console Handler
    if not quiet:
        console_level = logging.WARNING
        if verbose_count == 1:
            console_level = logging.INFO
        elif verbose_count >= 2:
            console_level = logging.DEBUG

        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        # Structured-ish format
        fmt = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
        console_handler.setFormatter(SanitizingFormatter(fmt))
        handlers.append(console_handler)

    # 2. File Handler
    if config.logging.file_enabled:
        file_path = config.logging.file_path or get_default_log_path()

        # Senior Security Strategy: Validate path safety to prevent traversal
        if not is_path_safe(file_path):
            print(f"Warning: Log path {file_path} is unsafe. Falling back to default.")
            file_path = get_default_log_path()

        # Use config level or elevate to DEBUG if -vv is passed
        if verbose_count >= 2:
            file_level = logging.DEBUG
        else:
            file_level = logging.INFO if config.logging.file_level == 1 else logging.DEBUG

        try:
            file_handler = logging.FileHandler(file_path, encoding="utf-8")
            file_handler.setLevel(file_level)
            fmt = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
            file_handler.setFormatter(SanitizingFormatter(fmt))
            handlers.append(file_handler)
        except Exception as e:
            print(f"Failed to initialize file logging at {file_path}: {e}")

    if handlers:
        _listener = logging.handlers.QueueListener(log_queue, *handlers, respect_handler_level=True)
        _listener.start()


def get_logger(name: str):
    """Returns a logger with the given name."""
    return logging.getLogger(name)


def shutdown_logging():
    """Safely stops the logging listener."""
    global _listener
    if _listener:
        try:
            _listener.stop()
        except Exception:
            pass
        _listener = None

    # Clear handlers from root logger
    logger = logging.getLogger()
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.handlers.QueueHandler):
            logger.removeHandler(handler)
