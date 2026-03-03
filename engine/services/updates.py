import datetime
import os
import threading
import time
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

                return {
                    "tag_name": data.get("tag_name"),
                    "html_url": data.get("html_url"),
                }
        except httpx.HTTPError as e:
            logger.debug(f"GitHub API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching update: {e}", exc_info=True)

        return None


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
