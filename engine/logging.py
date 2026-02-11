import logging
import logging.handlers
import queue
import re
from pathlib import Path
from typing import List, Optional

from platformdirs import user_log_dir

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

        return msg


def get_default_log_path() -> Path:
    """Get the default platform-specific log file path."""
    log_dir = Path(user_log_dir("Voice2Text", "alwat"))
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "voice2text.log"


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
