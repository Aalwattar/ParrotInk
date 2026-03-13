import logging
import unittest

from engine.config import Config
from engine.logging import configure_logging, set_global_level, shutdown_logging


class TestLoggingReload(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.config.logging.file_enabled = False  # Keep it simple for unit test
        configure_logging(self.config)

    def tearDown(self):
        shutdown_logging()

    def test_set_global_level_dynamic(self):
        """Verify that set_global_level changes the threshold of existing loggers."""
        # Initially level should be ERROR (default in Config)
        # However, configure_logging sets console to WARNING by default if not quiet.
        # Let's verify we can change it to DEBUG.

        set_global_level("verbose")

        # Since we use QueueHandler, the actual handlers are in the listener
        from engine.logging import _listener

        if _listener:
            for handler in _listener.handlers:
                self.assertEqual(handler.level, logging.DEBUG)
        else:
            self.fail("Logging listener not started")

    def test_set_global_level_invalid(self):
        """Verify that invalid levels fall back to ERROR safely."""
        set_global_level("invalid_level")
        from engine.logging import _listener

        if _listener:
            for handler in _listener.handlers:
                self.assertEqual(handler.level, logging.ERROR)
        else:
            self.fail("Logging listener not started")


if __name__ == "__main__":
    unittest.main()
