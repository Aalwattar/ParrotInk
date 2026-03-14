from unittest.mock import MagicMock, patch

from engine.services.updates import GitHubClient


def test_github_client_asset_extraction():
    """Verify that GitHubClient correctly extracts installer and checksum URLs."""
    client = GitHubClient("TestAgent")

    mock_response = {
        "tag_name": "v0.2.28",
        "html_url": "https://github.com/Aalwattar/ParrotInk/releases/tag/v0.2.28",
        "assets": [
            {
                "name": "ParrotInk.exe",
                "browser_download_url": "https://github.com/Aalwattar/ParrotInk/releases/download/v0.2.28/ParrotInk.exe",
            },
            {
                "name": "ParrotInk-Setup.exe",
                "browser_download_url": "https://github.com/Aalwattar/ParrotInk/releases/download/v0.2.28/ParrotInk-Setup.exe",
            },
            {
                "name": "ParrotInk-Setup.exe.sha256",
                "browser_download_url": "https://github.com/Aalwattar/ParrotInk/releases/download/v0.2.28/ParrotInk-Setup.exe.sha256",
            },
        ],
    }

    with patch("httpx.Client.get") as mock_get:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = mock_response
        mock_res.headers = {}
        mock_get.return_value = mock_res

        release = client.fetch_latest_release()

        assert release is not None
        assert release["tag_name"] == "v0.2.28"
        assert (
            release["installer_url"]
            == "https://github.com/Aalwattar/ParrotInk/releases/download/v0.2.28/ParrotInk-Setup.exe"
        )
        assert (
            release["checksum_url"]
            == "https://github.com/Aalwattar/ParrotInk/releases/download/v0.2.28/ParrotInk-Setup.exe.sha256"
        )


def test_github_client_missing_assets():
    """Verify behavior when expected assets are missing."""
    client = GitHubClient("TestAgent")

    # Missing Setup and Checksum
    mock_response = {
        "tag_name": "v0.2.28",
        "html_url": "https://github.com/Aalwattar/ParrotInk/releases/tag/v0.2.28",
        "assets": [
            {
                "name": "ParrotInk.exe",
                "browser_download_url": "https://github.com/Aalwattar/ParrotInk/releases/download/v0.2.28/ParrotInk.exe",
            }
        ],
    }

    with patch("httpx.Client.get") as mock_get:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = mock_response
        mock_res.headers = {}
        mock_get.return_value = mock_res

        release = client.fetch_latest_release()

        assert release is not None
        assert release["installer_url"] is None
        assert release["checksum_url"] is None
