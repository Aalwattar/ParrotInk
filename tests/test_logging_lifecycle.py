import pytest

from engine import logging as app_logging
from engine.config import Config


@pytest.fixture
def active_logging(tmp_path):
    config = Config()
    path = tmp_path / "lifecycle.log"
    config.logging.file_path = str(path)
    config.logging.file_level = "verbose"
    app_logging.configure_logging(config, quiet=True)
    listener = app_logging._listener
    try:
        yield config, path, listener
    finally:
        app_logging.shutdown_logging()
        if listener._thread is not None:
            listener.stop()
        for handler in listener.handlers:
            handler.close()


def test_app_exit_drains_pending_logs_and_closes_file(active_logging):
    _, path, listener = active_logging
    for index in range(50):
        app_logging.get_logger("LoggingExitTest").info("Pending event %s", index)

    app_logging.close_logging()

    assert listener._thread is None
    assert listener.handlers[0].stream is None
    assert app_logging._listener is None
    assert "Pending event 49" in path.read_text(encoding="utf-8")


def test_reconfiguration_stops_previous_worker_and_releases_file(active_logging):
    config, path, previous = active_logging
    app_logging.get_logger("LoggingReloadTest").info("Before reconfiguration")

    app_logging.configure_logging(config, quiet=True)

    assert previous._thread is None
    assert previous.handlers[0].stream is None
    assert "Before reconfiguration" in path.read_text(encoding="utf-8")
