import datetime
import hashlib
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, Optional

import httpx

from packaging import version

from ..logging import get_logger
from ..ui_utils import get_app_version

logger = get_logger("Updates")

GITHUB_API_URL = "https://api.github.com/repos/Aalwattar/ParrotInk/releases/latest"


class GitHubClient:
    """Handles communication with the GitHub API."""

    def __init__(self, user_agent: str):
        self.user_agent = user_agent

    def fetch_latest_release(self) -> Optional[dict]:
        """Fetches the latest release info from GitHub.

        Returns:
            Optional[dict]: A dictionary containing 'tag_name' and 'html_url',
                             or None if no release found or error occurred.
        """
        headers = {"User-Agent": self.user_agent}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(GITHUB_API_URL, headers=headers)

                # Proactive Rate Limit Check (Before status handling)
                remaining = response.headers.get("X-RateLimit-Remaining")
                if remaining and remaining.isdigit() and int(remaining) == 0:
                    reset_epoch = response.headers.get("X-RateLimit-Reset")
                    if reset_epoch and reset_epoch.isdigit():
                        res_time = datetime.datetime.fromtimestamp(int(reset_epoch)).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        logger.warning(f"GitHub Rate Limit hit. Resets at {res_time}")

                if response.status_code == 403:
                    error_data = {}
                    try:
                        error_data = response.json()
                    except Exception:
                        pass

                    msg = error_data.get("message", "Forbidden")
                    logger.warning(f"GitHub API 403: {msg}")
                    return None

                if response.status_code == 404:
                    logger.debug("No GitHub releases found (404).")
                    return None

                response.raise_for_status()
                data = response.json()

                assets = data.get("assets", [])
                installer_url = None
                checksum_url = None

                for asset in assets:
                    name = asset.get("name", "")
                    if name == "ParrotInk-Setup.exe":
                        installer_url = asset.get("browser_download_url")
                    elif name == "ParrotInk-Setup.exe.sha256":
                        checksum_url = asset.get("browser_download_url")

                return {
                    "tag_name": data.get("tag_name"),
                    "html_url": data.get("html_url"),
                    "installer_url": installer_url,
                    "checksum_url": checksum_url,
                }
        except httpx.HTTPError as e:
            logger.debug(f"GitHub API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching update: {e}", exc_info=True)

        return None


class BITSClient:
    """Manages Background Intelligent Transfer Service (BITS) via PowerShell."""

    JOB_NAME = "ParrotInk Update"

    def start_download(self, url: str, dest_path: str) -> bool:
        """Initiates an asynchronous background download."""
        logger.info(f"Starting BITS download: {url} -> {dest_path}")
        # -Asynchronous: returns control to Python immediately
        # -Priority: Normal (uses idle bandwidth)
        ps_command = (
            f'Start-BitsTransfer -Source "{url}" -Destination "{dest_path}" '
            f'-DisplayName "{self.JOB_NAME}" -Asynchronous -Priority Normal'
        )
        try:
            subprocess.run(["powershell", "-Command", ps_command], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start BITS transfer: {e.stderr.decode()}")
            return False

    def get_status(self) -> dict:
        """Queries the status of the update job.

        Returns:
            dict: {state: str, percent: int, is_complete: bool}
        """
        ps_command = (
            f'Get-BitsTransfer -DisplayName "{self.JOB_NAME}" | '
            "Select-Object JobState, BytesTransferred, TotalBytesToTransfer | "
            "ForEach-Object { 'JobState=' + $_.JobState + ';BytesTransferred=' + "
            "$_.BytesTransferred + ';TotalBytesToTransfer=' + $_.TotalBytesToTransfer }"
        )
        try:
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                check=True,
                capture_output=True,
                text=True,
            )
            output = result.stdout.strip()
            if not output:
                return {"state": "NotFound", "percent": 0, "is_complete": False}

            # Parse simple semicolon-delimited output
            data = dict(item.split("=") for item in output.split(";") if "=" in item)
            state = data.get("JobState", "Unknown")
            transferred = int(data.get("BytesTransferred", 0))
            total = int(data.get("TotalBytesToTransfer", 0))

            percent = 0
            if total > 0:
                percent = int((transferred / total) * 100)

            return {
                "state": state,
                "percent": percent,
                "is_complete": state == "Transferred",
            }
        except Exception as e:
            logger.debug(f"Error querying BITS status: {e}")
            return {"state": "Error", "percent": 0, "is_complete": False}

    def complete_download(self) -> bool:
        """Finalizes the transfer and moves the file to the destination."""
        logger.info("Completing BITS transfer...")
        ps_command = f'Get-BitsTransfer -DisplayName "{self.JOB_NAME}" | Complete-BitsTransfer'
        try:
            subprocess.run(["powershell", "-Command", ps_command], check=True, capture_output=True)
            return True
        except Exception as e:
            logger.error(f"Failed to complete BITS transfer: {e}")
            return False

    def cancel_download(self):
        """Cancels any existing update job."""
        ps_command = f'Get-BitsTransfer -DisplayName "{self.JOB_NAME}" | Remove-BitsTransfer'
        try:
            subprocess.run(["powershell", "-Command", ps_command], capture_output=True)
        except Exception:
            pass


class ChecksumVerifier:
    """Verifies the integrity of downloaded files using SHA256."""

    def verify(self, file_path: Path | str, expected_hash: str) -> bool:
        """Computes the SHA256 of the file and compares it to the expected hash.

        Args:
            file_path: Path to the file to verify.
            expected_hash: The hex-encoded SHA256 string to match against.
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read in 4KB chunks
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)

            actual_hash = sha256_hash.hexdigest().lower()
            expected_hash = expected_hash.strip().lower()

            if actual_hash == expected_hash:
                logger.info(f"Checksum verification passed for {file_path}")
                return True

            logger.error(
                f"Checksum mismatch for {file_path}. Expected: {expected_hash}, Got: {actual_hash}"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to verify checksum for {file_path}: {e}")
            return False


class UpdateManager:
    """Manages version comparison and background polling logic."""

    def __init__(
        self, on_update_available: Callable[[str, str], None], stop_event: threading.Event
    ):
        """
        Args:
            on_update_available: Callback(new_version_string, release_url)
            stop_event: Global shutdown signal to prevent races.
        """
        self.on_update_available = on_update_available
        self.stop_event = stop_event
        self.local_version = get_app_version()
        self.client = GitHubClient(f"ParrotInk/{self.local_version} (Update Checker)")

        self._thread: Optional[threading.Thread] = None
        self._last_check_time = 0.0
        self._check_interval = 24 * 3600  # 24 hours

    def start(self):
        """Starts the background update checker thread."""
        if self._thread and self._thread.is_alive():
            return

        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="UpdateChecker")
        self._thread.start()

    def _run_loop(self):
        """Background loop that polls GitHub periodically."""
        # Initial check on startup
        self.check_now()

        while not self.stop_event.is_set():
            # Wait for 1 hour between "is_set" checks, but wait total 24h between API calls
            # Use small sleeps to remain responsive to shutdown
            for _ in range(3600):
                if self.stop_event.is_set():
                    return
                time.sleep(1)

            if time.time() - self._last_check_time > self._check_interval:
                self.check_now()

    def check_now(self):
        """Perform a single version check."""
        if self.stop_event.is_set():
            return

        logger.debug("Checking for updates on GitHub...")
        release = self.client.fetch_latest_release()
        self._last_check_time = time.time()

        if not release:
            return

        remote_tag = release.get("tag_name")
        remote_url = release.get("html_url")

        if not remote_tag or not remote_url:
            return

        try:
            # Robust comparison using packaging.version
            local_v = version.parse(self.local_version)
            remote_v = version.parse(remote_tag.lstrip("v"))

            if remote_v > local_v:
                logger.info(f"Update available: {remote_tag} (current: {self.local_version})")
                # Final safety check before calling UI
                if not self.stop_event.is_set():
                    self.on_update_available(remote_tag, remote_url)
            else:
                logger.debug(f"Application is up to date (current: {self.local_version})")
        except version.InvalidVersion as e:
            logger.warning(f"Failed to parse version strings: {e}")
