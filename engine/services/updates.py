import ctypes
import datetime
import hashlib
import os
import subprocess
import sys
import tempfile
import threading
import time
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Optional

import httpx

from engine.logging import get_logger
from engine.ui_utils import get_app_version
from packaging import version

logger = get_logger("Updates")

GITHUB_API_URL = "https://api.github.com/repos/Aalwattar/ParrotInk/releases/latest"


class UpdateState(Enum):
    """Internal states for the UpdateManager."""

    IDLE = auto()
    CHECKING = auto()
    UPDATE_AVAILABLE = auto()
    DOWNLOADING = auto()
    READY_TO_INSTALL = auto()
    ERROR = auto()


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
            subprocess.run(
                ["powershell", "-Command", ps_command],
                check=True,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
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
            f'Get-BitsTransfer -Name "{self.JOB_NAME}" | '
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
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            output = result.stdout.strip()
            if not output:
                return {"state": "NotFound", "percent": 0, "is_complete": False}

            # If there are multiple jobs, just take the first one
            first_job = output.splitlines()[0].strip()

            # Parse simple semicolon-delimited output
            data = {}
            for item in first_job.split(";"):
                if "=" in item:
                    k, v = item.split("=", 1)
                    data[k] = v

            state = data.get("JobState", "Unknown")
            transferred_str = data.get("BytesTransferred", "0").strip()
            total_str = data.get("TotalBytesToTransfer", "0").strip()

            transferred = int(transferred_str) if transferred_str else 0
            total = int(total_str) if total_str else 0

            percent = 0
            if total > 0:
                percent = int((transferred / total) * 100)
            elif state == "Transferred":
                percent = 100
            elif transferred > 0:
                # GitHub release redirects sometimes hide Content-Length from BITS.
                # We estimate against ~60MB to provide meaningful UX instead of 0%.
                percent = min(99, int((transferred / (60 * 1024 * 1024)) * 100))

            return {
                "state": state,
                "percent": percent,
                "is_complete": state == "Transferred",
            }
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr if e.stderr else str(e)
            if "Cannot find a BITS transfer" in err_msg or "Cannot find a BITS job" in err_msg:
                return {"state": "NotFound", "percent": 0, "is_complete": False}
            logger.debug(f"Error querying BITS status (CalledProcessError): {err_msg}")
            return {"state": "Error", "percent": 0, "is_complete": False}
        except Exception as e:
            logger.debug(f"Error querying BITS status: {e}")
            return {"state": "Error", "percent": 0, "is_complete": False}

    def complete_download(self) -> bool:
        """Finalizes the transfer and moves the file to the destination."""
        logger.info("Completing BITS transfer...")
        ps_command = f'Get-BitsTransfer -Name "{self.JOB_NAME}" | Complete-BitsTransfer'
        try:
            subprocess.run(
                ["powershell", "-Command", ps_command],
                check=True,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to complete BITS transfer: {e}")
            return False

    def cancel_download(self):
        """Cancels any existing update job."""
        ps_command = f'Get-BitsTransfer -Name "{self.JOB_NAME}" | Remove-BitsTransfer'
        try:
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
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
        self,
        on_update_available: Callable[[str, str, UpdateState, int], None],
        stop_event: threading.Event,
    ):
        """
        Args:
            on_update_available: Callback(new_version, url, state, percent)
            stop_event: Global shutdown signal.
        """
        self.on_update_available = on_update_available
        self.stop_event = stop_event
        self.local_version = get_app_version()
        self.client = GitHubClient(f"ParrotInk/{self.local_version} (Update Checker)")
        self.bits = BITSClient()
        self.verifier = ChecksumVerifier()

        self.state = UpdateState.IDLE
        self.latest_release: Optional[dict] = None
        self.download_percent = 0
        self.installer_path: Optional[Path] = None

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
        """Background loop that polls GitHub and BITS status."""
        # Initial check on startup
        self.check_now()

        while not self.stop_event.is_set():
            # Responsive polling
            if self.state == UpdateState.DOWNLOADING:
                self._poll_bits()
                time.sleep(5)  # Poll more frequently during download
            else:
                # Wait for 1 hour between "is_set" checks for general polling
                for _ in range(3600):
                    if self.stop_event.is_set():
                        return
                    time.sleep(1)

                if time.time() - self._last_check_time > self._check_interval:
                    self.check_now()

    def _poll_bits(self):
        """Checks BITS status and handles completion/verification."""
        status = self.bits.get_status()
        self.download_percent = status["percent"]

        if status["is_complete"]:
            self._finalize_download()
        elif status["state"] in ["Error", "TransientError"]:
            logger.warning(f"BITS download error: {status['state']}")
            # Revert to available so user can try again (or we can retry later)
            self.state = UpdateState.UPDATE_AVAILABLE
            self.on_update_available(
                self.latest_release["tag_name"],
                self.latest_release["html_url"],
                self.state,
                0,
            )
        else:
            # Update UI with progress
            self.on_update_available(
                self.latest_release["tag_name"],
                self.latest_release["html_url"],
                self.state,
                self.download_percent,
            )

    def _verify_installer(self) -> bool:
        """Fetch checksum and verify the current installer_path. Returns True if valid."""
        if not self.latest_release or not self.installer_path or not self.installer_path.exists():
            return False

        checksum_url = self.latest_release.get("checksum_url")
        if not checksum_url:
            # If no checksum is provided by the provider, we consider it "valid" if it exists
            return True

        try:
            # Download checksum file
            res = httpx.get(checksum_url, timeout=10.0, follow_redirects=True)
            res.raise_for_status()
            # SHA256 file usually contains: <hash> <filename>
            expected_hash = res.text.split()[0]

            return self.verifier.verify(self.installer_path, expected_hash)
        except Exception as e:
            logger.error(f"Verification check failed: {e}")
            return False

    def _finalize_download(self):
        """Completes the BITS transfer and verifies checksum."""
        if not self.latest_release or not self.installer_path:
            return

        if not self.bits.complete_download():
            return

        if self._verify_installer():
            self.state = UpdateState.READY_TO_INSTALL
        else:
            self.state = UpdateState.ERROR
            logger.error("Update verification failed.")

        self.on_update_available(
            self.latest_release["tag_name"],
            self.latest_release["html_url"],
            self.state,
            100,
        )

    def check_now(self):
        """Perform a single version check and trigger download if needed."""
        if self.stop_event.is_set():
            return

        self.state = UpdateState.CHECKING
        logger.debug("Checking for updates on GitHub...")
        release = self.client.fetch_latest_release()
        self._last_check_time = time.time()

        if not release:
            self.state = UpdateState.IDLE
            return

        remote_tag = release.get("tag_name")
        remote_url = release.get("html_url")
        installer_url = release.get("installer_url")

        if not remote_tag or not remote_url:
            self.state = UpdateState.IDLE
            return

        try:
            local_v = version.parse(self.local_version)
            remote_v = version.parse(remote_tag.lstrip("v"))

            if remote_v > local_v:
                logger.info(f"Update available: {remote_tag} (current: {self.local_version})")
                self.latest_release = release

                # Auto-start BITS download if installer URL is present
                if installer_url:
                    temp_dir = Path(tempfile.gettempdir())
                    self.installer_path = temp_dir / f"ParrotInk-Setup-{remote_tag}.exe"

                    # Check if existing file is already valid to avoid redownloading
                    if self.installer_path.exists() and self._verify_installer():
                        logger.info(f"Existing valid installer found: {self.installer_path}")
                        self.state = UpdateState.READY_TO_INSTALL
                    else:
                        # Ensure we don't have a stale job or old file
                        self.bits.cancel_download()
                        if self.installer_path.exists():
                            try:
                                self.installer_path.unlink()
                            except Exception:
                                pass

                        if self.bits.start_download(installer_url, str(self.installer_path)):
                            self.state = UpdateState.DOWNLOADING
                        else:
                            self.state = UpdateState.UPDATE_AVAILABLE
                else:
                    self.state = UpdateState.UPDATE_AVAILABLE

                if not self.stop_event.is_set():
                    self.on_update_available(remote_tag, remote_url, self.state, 0)
            else:
                logger.debug(f"Application is up to date (current: {self.local_version})")
                self.state = UpdateState.IDLE
        except version.InvalidVersion as e:
            logger.warning(f"Failed to parse version strings: {e}")
            self.state = UpdateState.IDLE

    def sanitize_for_external_process(self) -> None:
        """Resets PyInstaller-specific environment state to prevent child process contamination.

        This is critical for Windows frozen apps because they modify the DLL search path.
        If a child (like the installer) or grandchild inherits this search path,
        it may fail to load its own DLLs if they conflict with the old version.

        NOTE: Modifies os.environ in place so ShellExecuteW inherits the changes.
        """
        if sys.platform == "win32":
            # Senior Architecture: Reset the library search path.
            # PyInstaller bootloader calls SetDllDirectoryW(MEIPASS).
            # Passing None restores the default Windows search order.
            ctypes.windll.kernel32.SetDllDirectoryW(None)

        # Scrub PATH of any entries pointing into our temporary extraction directory
        mei = getattr(sys, "_MEIPASS", None)
        if mei:
            mei_norm = os.path.normcase(os.path.abspath(mei))
            os.environ["PATH"] = os.pathsep.join(
                p
                for p in os.environ.get("PATH", "").split(os.pathsep)
                if p and not os.path.normcase(os.path.abspath(p)).startswith(mei_norm)
            )

        # Remove the extraction variable itself
        os.environ.pop("_MEIPASS", None)

        # Instruct child PyInstaller processes to reset their own environment
        os.environ["PYINSTALLER_RESET_ENVIRONMENT"] = "1"

    def unblock_installer(self) -> bool:
        """Removes the Mark of the Web (Zone.Identifier Alternate Data Stream) from the installer.

        This prevents Windows SmartScreen, Software Restriction Policies (SRP), or AppLocker
        from blocking execution of the downloaded installer.
        """
        if sys.platform != "win32" or not self.installer_path or not self.installer_path.exists():
            return False

        installer_path = str(self.installer_path)
        logger.info(f"Attempting to unblock installer file: {installer_path}")

        # Method 1: Try PowerShell's Unblock-File
        try:
            subprocess.run(
                ["powershell", "-Command", f'Unblock-File -Path "{installer_path}"'],
                check=True,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            logger.info("Successfully unblocked installer file using PowerShell Unblock-File")
            return True
        except Exception as e:
            logger.warning(f"PowerShell Unblock-File failed: {e}. Trying fallback.")

        # Method 2: Direct removal of Zone.Identifier Alternate Data Stream via Python
        try:
            ads_path = installer_path + ":Zone.Identifier"
            os.unlink(ads_path)
            logger.info("Successfully unblocked installer file via direct unlink of ADS")
            return True
        except FileNotFoundError:
            logger.debug("No Zone.Identifier stream found (file may already be unblocked).")
            return True
        except Exception as ex:
            logger.warning(f"Failed to remove Zone.Identifier stream: {ex}")

        return False

    def install_now(self) -> bool:
        """Launches the installer and returns True on success.

        Uses ShellExecuteW to ensure the installer survives the parent application
        closure and can trigger UAC elevation if required. Deterministically
        scrubs the inherited PyInstaller environment to prevent DLL search path
        poisoning in the new version.
        """
        if self.state != UpdateState.READY_TO_INSTALL or not self.installer_path:
            return False

        installer_path = str(self.installer_path)
        current_pid = os.getpid()
        logger.info(f"Launching decoupled installer: {installer_path} (PID: {current_pid})")

        try:
            # Unblock the downloaded installer to bypass Windows SmartScreen / SRP policies
            self.unblock_installer()

            # Senior Architecture: Prevent "DLL Search Path Poisoning"
            # We must reset the DLL search path and scrub _MEIPASS from the environment
            # so the installer and the resulting new app don't try to load DLLs
            # from the old version's temporary directory.
            self.sanitize_for_external_process()

            if sys.platform == "win32":
                # SW_SHOWNORMAL = 1
                # ShellExecuteW delegates to Explorer.exe, decoupling the process
                # and allowing for UAC elevation prompts.
                # Parameters: /SILENT (Inno Setup) /pid=xxxx (Custom)
                ret = ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "open",
                    installer_path,
                    f"/SILENT /pid={current_pid}",
                    None,
                    1,
                )
                # Returns value > 32 on success
                if ret <= 32:
                    logger.error(f"ShellExecuteW failed with code: {ret}")
                    return False
            else:
                # Fallback for non-Windows (unlikely in this context)
                subprocess.Popen(
                    [installer_path, "/SILENT", f"/pid={current_pid}"],
                    creationflags=subprocess.DETACHED_PROCESS,
                    shell=False,
                )

            return True
        except Exception as e:
            logger.error(f"Failed to launch decoupled installer: {e}")
            return False
