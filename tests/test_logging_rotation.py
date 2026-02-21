import time
from unittest.mock import MagicMock

import pytest

from engine.logging import configure_logging, get_logger, shutdown_logging


@pytest.fixture
def temp_log_dir(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


def test_logging_rotation_creation(temp_log_dir):
    """Verify that the log file is created and rotated when full."""
    log_file = temp_log_dir / "test.log"

    # Configure logging with tiny max bytes to trigger rotation quickly
    mock_config = MagicMock()
    mock_config.logging.file_enabled = True
    mock_config.logging.file_path = str(log_file)
    mock_config.logging.file_level = "verbose"
    mock_config.logging.file_max_bytes = 100  # 100 bytes
    mock_config.logging.file_backup_count = 2

    configure_logging(mock_config, quiet=True)

    logger = get_logger("TestRotation")

    # 1. Write first batch
    logger.debug("Initial log message that is definitely more than 100 bytes long for rotation.")

    # Give the QueueListener a moment to process
    time.sleep(0.2)

    assert log_file.exists()

    # 2. Write more to trigger rotation
    for i in range(5):
        logger.debug(f"Rotation trigger {i} - padding to ensure we exceed 100 bytes per message.")
        time.sleep(0.05)

    time.sleep(0.5)  # Wait for processing

    # Check for rotated files
    rotated_file = temp_log_dir / "test.log.1"
    assert rotated_file.exists(), f"Rotated file {rotated_file} should exist"

    shutdown_logging()


def test_logging_disabled(temp_log_dir):
    """Verify that no file is created when logging is disabled."""
    log_file = temp_log_dir / "disabled.log"

    mock_config = MagicMock()
    mock_config.logging.file_enabled = False
    mock_config.logging.file_path = str(log_file)

    configure_logging(mock_config, quiet=True)
    logger = get_logger("TestDisabled")
    logger.info("This should not be in a file.")

    time.sleep(0.2)
    assert not log_file.exists()

    shutdown_logging()
