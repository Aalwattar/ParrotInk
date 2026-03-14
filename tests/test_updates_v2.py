import threading
from enum import Enum, auto
from unittest.mock import MagicMock, patch

from engine.services.updates import BITSClient, ChecksumVerifier, GitHubClient, UpdateManager


class UpdateState(Enum):
    IDLE = auto()
    CHECKING = auto()
    UPDATE_AVAILABLE = auto()
    DOWNLOADING = auto()
    READY_TO_INSTALL = auto()
    ERROR = auto()


def test_update_manager_lifecycle():
    """Verify the high-level state transitions of the UpdateManager."""
    on_available = MagicMock()
    stop_event = threading.Event()

    with (
        patch("engine.services.updates.GitHubClient") as mock_client_cls,
        patch("engine.services.updates.BITSClient") as mock_bits_cls,
        patch("engine.services.updates.ChecksumVerifier") as mock_verifier_cls,
    ):
        mock_client = mock_client_cls.return_value
        mock_bits = mock_bits_cls.return_value
        mock_verifier = mock_verifier_cls.return_value

        manager = UpdateManager(on_available, stop_event)

        # 1. Update found
        mock_client.fetch_latest_release.return_value = {
            "tag_name": "v9.9.9",
            "html_url": "https://test",
            "installer_url": "https://test/setup.exe",
            "checksum_url": "https://test/setup.exe.sha256",
        }

        # 2. Check for updates
        manager.check_now()

        # Verify BITS download started automatically
        mock_bits.start_download.assert_called_once()
        assert manager.state.name == "DOWNLOADING"

        # 3. Simulate download completion
        mock_bits.get_status.return_value = {
            "state": "Transferred",
            "percent": 100,
            "is_complete": True,
        }

        # Mock checksum download and verification
        with patch("httpx.get") as mock_http_get:
            mock_http_get.return_value = MagicMock(text="mock_hash", status_code=200)
            mock_verifier.verify.return_value = True

            # Run one poll cycle
            manager._poll_bits()

            mock_bits.complete_download.assert_called_once()
            assert manager.state.name == "READY_TO_INSTALL"
            assert on_available.call_count == 2


def test_checksum_verifier_success(tmp_path):
    """Verify that ChecksumVerifier correctly matches valid hashes."""
    file_path = tmp_path / "test.exe"
    file_path.write_bytes(b"test content")

    # Expected SHA256 for "test content"
    expected_hash = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"

    verifier = ChecksumVerifier()
    assert verifier.verify(file_path, expected_hash) is True


def test_checksum_verifier_failure(tmp_path):
    """Verify that ChecksumVerifier rejects invalid hashes."""
    file_path = tmp_path / "test.exe"
    file_path.write_bytes(b"wrong content")

    expected_hash = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"

    verifier = ChecksumVerifier()
    assert verifier.verify(file_path, expected_hash) is False


def test_bits_client_start_job():
    """Verify that BITSClient correctly formats the Start-BitsTransfer command."""
    client = BITSClient()
    url = "https://example.com/setup.exe"
    dest = "C:\\temp\\setup.exe"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(return_code=0)
        client.start_download(url, dest)

        # Verify the command
        args = mock_run.call_args[0][0]
        assert "Start-BitsTransfer" in args[2]
        assert f'-Source "{url}"' in args[2]
        assert f'-Destination "{dest}"' in args[2]
        assert "-Asynchronous" in args[2]
        assert '-DisplayName "ParrotInk Update"' in args[2]


def test_bits_client_get_status():
    """Verify that BITSClient correctly parses the status output."""
    client = BITSClient()

    # Mock output for Get-BitsTransfer
    # JobState: Transferred, BytesTransferred: 100, TotalBytesToTransfer: 100
    mock_stdout = "JobState=Transferred;BytesTransferred=1048576;TotalBytesToTransfer=1048576"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_stdout, returncode=0)
        status = client.get_status()

        assert status["state"] == "Transferred"
        assert status["percent"] == 100
        assert status["is_complete"] is True


def test_bits_client_get_status_in_progress():
    """Verify parsing for a job in progress."""
    client = BITSClient()
    mock_stdout = "JobState=Transferring;BytesTransferred=524288;TotalBytesToTransfer=1048576"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_stdout, returncode=0)
        status = client.get_status()

        assert status["state"] == "Transferring"
        assert status["percent"] == 50
        assert status["is_complete"] is False


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
