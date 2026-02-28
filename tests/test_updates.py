import threading
from unittest.mock import MagicMock, patch

import pytest

from engine.services.updates import GitHubClient, UpdateManager


@pytest.fixture
def mock_httpx():
    with patch("httpx.Client") as mock:
        yield mock


def test_github_client_success(mock_httpx):
    # Mock successful GitHub response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "tag_name": "v1.2.3",
        "html_url": "https://github.com/test/release",
    }
    mock_response.headers = {"X-RateLimit-Remaining": "50"}

    # Configure mock context manager
    mock_httpx.return_value.__enter__.return_value.get.return_value = mock_response

    client = GitHubClient("TestAgent")
    result = client.fetch_latest_release()

    assert result["tag_name"] == "v1.2.3"
    assert result["html_url"] == "https://github.com/test/release"


def test_github_client_rate_limited(mock_httpx):
    mock_response = MagicMock()
    mock_response.headers = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "123456"}
    mock_httpx.return_value.__enter__.return_value.get.return_value = mock_response

    client = GitHubClient("TestAgent")
    assert client.fetch_latest_release() is None


def test_version_comparison_logic():
    stop_event = threading.Event()
    callback = MagicMock()

    # Mock fetch_latest_release to return a newer version
    with patch("engine.services.updates.get_app_version", return_value="0.1.0"):
        with patch.object(GitHubClient, "fetch_latest_release") as mock_fetch:
            mock_fetch.return_value = {"tag_name": "v0.2.0", "html_url": "http://test"}

            manager = UpdateManager(callback, stop_event)
            manager._check_now()

            callback.assert_called_once_with("v0.2.0", "http://test")


def test_version_comparison_older_remote():
    stop_event = threading.Event()
    callback = MagicMock()

    with patch("engine.services.updates.get_app_version", return_value="0.2.0"):
        with patch.object(GitHubClient, "fetch_latest_release") as mock_fetch:
            mock_fetch.return_value = {"tag_name": "v0.1.5", "html_url": "http://test"}

            manager = UpdateManager(callback, stop_event)
            manager._check_now()

            callback.assert_not_called()
