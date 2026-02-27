import asyncio
import time
from typing import Callable, Optional

from engine.app_types import AppState
from engine.audio.adapter import AudioAdapter
from engine.config import Config
from engine.constants import STATUS_CONNECTING, STATUS_FAILED, STATUS_RETRYING
from engine.logging import get_logger
from engine.transcription.base import BaseProvider
from engine.transcription.factory import TranscriptionFactory

logger = get_logger("Connection")


class ConnectionManager:
    """
    Manages the lifecycle of transcription providers, including
    connection management, session rotation, and backoff logic.
    """

    def __init__(
        self,
        config: Config,
        on_partial: Callable[[str], None],
        on_final: Callable[[str], None],
        set_state_cb: Callable[[AppState], None],
        on_status_cb: Optional[Callable[[str], None]] = None,
    ):
        self._config = config
        self.on_partial = on_partial
        self.on_final = on_final
        self.set_state = set_state_cb
        self.on_status = on_status_cb

        self.provider: Optional[BaseProvider] = None
        self.audio_adapter: Optional[AudioAdapter] = None

        self._session_start_time = 0.0
        self._rotation_pending = False
        self._backoff_delay = self.config.audio.initial_backoff_seconds
        self._last_fail_time = 0.0
        self._last_activity_time = 0.0
        self._idle_timer_task: Optional[asyncio.Task] = None
        self._stop_lock = asyncio.Lock()

    @property
    def config(self) -> Config:
        return self._config

    @config.setter
    def config(self, new_config: Config):
        """
        Updates the internal configuration.
        If the provider has changed, we prepare for rotation or restart.
        """
        old_provider = self._config.transcription.provider
        new_provider = new_config.transcription.provider
        self._config = new_config

        if old_provider != new_provider:
            logger.info(f"Provider changed from {old_provider} to {new_provider}")
            # We don't stop immediately if listening (to avoid stutter),
            # but ensure_connected will catch it.
            # If idle, we can mark for rotation to force a fresh connect on next use.
            self._rotation_pending = True

    async def ensure_connected(self, is_listening: bool):
        """
        Idempotent connection management.
        Ensures the provider is connected based on connection_mode.
        """

        # Always cancel any pending idle timer if we are ensuring connection
        if self._idle_timer_task:
            self._idle_timer_task.cancel()
            self._idle_timer_task = None

        if self.provider and self.provider.is_running:
            # Check for rotation
            if self.config.transcription.provider == "openai":
                age = time.time() - self._session_start_time
                rotation_threshold = self.config.providers.openai.core.session_rotation_seconds
                if age > rotation_threshold:
                    if is_listening:
                        if not self._rotation_pending:
                            logger.info(
                                f"Session age > {rotation_threshold}s, marking rotation pending."
                            )
                            self._rotation_pending = True
                    else:
                        logger.info(f"Rotating OpenAI session due to age ({age:.1f}s).")
                        await self.stop_provider()
                        # Fall through to reconnect
                elif self._rotation_pending and not is_listening:
                    logger.info("Performing pending OpenAI session rotation.")
                    await self.stop_provider()
                    self._rotation_pending = False
                    # Fall through to reconnect

            # Check if provider type matches configuration
            if self.provider and self.provider.get_type() != self.config.transcription.provider:
                logger.info(
                    f"Provider type mismatch ({self.provider.get_type()} != "
                    f"{self.config.transcription.provider}). Reconnecting..."
                )
                if not is_listening:
                    await self.stop_provider()
                    # Fall through to reconnect
                else:
                    # If listening, we can't switch safely mid-stream
                    pass

        if self.provider and self.provider.is_running:
            return

        # Initialize provider if not exists
        if not self.provider:
            self.provider = TranscriptionFactory.create(
                self.config,
                on_partial=self.on_partial,
                on_final=self.on_final,
                on_status=self.on_status,
            )
            self.audio_adapter = AudioAdapter(
                capture_rate_hz=self.config.audio.capture_sample_rate,
                provider_spec=self.provider.get_audio_spec(),
                energy_threshold=self.config.audio.voice_activity_threshold,
            )

        # Connect
        now = time.time()
        time_since_fail = now - self._last_fail_time
        if time_since_fail < self._backoff_delay:
            wait_time = self._backoff_delay - time_since_fail
            logger.warning(f"Connection backoff active. Waiting {wait_time:.1f}s...")
            await asyncio.sleep(wait_time)

        logger.info(f"Connecting to {self.config.transcription.provider}...")
        self.set_state(AppState.CONNECTING)
        if self.on_status:
            self.on_status(STATUS_CONNECTING)

        retry_count = self.config.audio.max_retries
        current_attempt = 0

        while current_attempt < retry_count:
            current_attempt += 1
            try:
                logger.debug(
                    f"Starting provider {self.config.transcription.provider} "
                    f"(Attempt {current_attempt}/{retry_count})..."
                )
                async with asyncio.timeout(self.config.audio.connection_timeout_seconds):
                    await self.provider.start()
                logger.debug("Provider started.")
                self._session_start_time = time.time()
                self._rotation_pending = False
                self._backoff_delay = self.config.audio.initial_backoff_seconds
                logger.info("Connected successfully.")

                # If we are NOT in the middle of a listening command, transition to IDLE
                if not is_listening:
                    self.set_state(AppState.IDLE)

                # Success - break loop
                return

            except (TimeoutError, asyncio.CancelledError, Exception) as e:
                is_last_attempt = current_attempt >= retry_count
                error_msg = f"Connection attempt {current_attempt} failed: {type(e).__name__} - {e}"

                if isinstance(e, asyncio.CancelledError) and not is_last_attempt:
                    logger.warning(f"{error_msg}. Retrying...")
                    if self.on_status:
                        self.on_status(STATUS_RETRYING)
                elif is_last_attempt:
                    logger.error(f"{error_msg}. Giving up.")
                    if self.on_status:
                        self.on_status(STATUS_FAILED)
                else:
                    wait_s = self.config.audio.initial_backoff_seconds
                    logger.warning(f"{error_msg}. Retrying in {wait_s}s...")
                    if self.on_status:
                        self.on_status(STATUS_RETRYING)

                if is_last_attempt:
                    self._last_fail_time = time.time()
                    self._backoff_delay = min(
                        self._backoff_delay * 2, self.config.audio.max_backoff_seconds
                    )
                    self.provider = None
                    self.audio_adapter = None
                    self.set_state(AppState.ERROR)
                    # Force a cleanup of the provider if it exists
                    if self.provider:
                        asyncio.create_task(self.stop_provider())
                    raise

                await asyncio.sleep(self.config.audio.initial_backoff_seconds)

    async def stop_provider(self):
        """Stops the current provider and cleans up adapters."""
        async with self._stop_lock:
            if self._idle_timer_task:
                self._idle_timer_task.cancel()
                self._idle_timer_task = None

            if self.provider:
                try:
                    async with asyncio.timeout(self.config.audio.connection_timeout_seconds):
                        await self.provider.stop()
                except Exception as e:
                    logger.error(f"Error stopping provider ({type(e).__name__}): {e}")

                if self.audio_adapter:
                    self.audio_adapter.close()

                self.provider = None
                self.audio_adapter = None

    def start_idle_timer(self):
        """Starts the idle timeout timer if configured."""
        if self.config.audio.connection_mode == "warm":
            self._last_activity_time = time.time()
            if not self._idle_timer_task or self._idle_timer_task.done():
                self._idle_timer_task = asyncio.create_task(self._idle_timer_check())

        # I3: Check for rotation immediately after stopping (during idle)
        if self._rotation_pending:
            logger.info("Session rotation pending. Scheduling immediate rotation during idle.")
            asyncio.create_task(self.ensure_connected(is_listening=False))

    async def _idle_timer_check(self):
        """Task that waits for idle timeout and closes connection."""
        timeout = self.config.audio.warm_idle_timeout_seconds
        try:
            while True:
                now = time.time()
                elapsed = now - self._last_activity_time
                if elapsed >= timeout:
                    if self.provider and self.provider.is_running:
                        logger.info(f"Closing warm connection after {timeout}s idle.")
                        await self.stop_provider()
                    break
                await asyncio.sleep(min(1.0, timeout - elapsed))
        except asyncio.CancelledError:
            pass

    async def shutdown(self):
        """Final cleanup of all connection resources."""
        await self.stop_provider()
