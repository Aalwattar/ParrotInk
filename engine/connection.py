import asyncio
import contextlib
import time
from typing import Callable, Optional

from engine.app_types import AppState
from engine.audio.adapter import AudioAdapter
from engine.config import Config
from engine.constants import STATUS_CONNECTING, STATUS_FAILED, STATUS_READY, STATUS_RETRYING
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

        # Concurrency & Lifecycle
        self._state_lock = asyncio.Lock()
        self._connect_task: Optional[asyncio.Task] = None
        self._generation = 0

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

        # Pre-check rotation/type-mismatch (may trigger an immediate stop_provider)
        if self.provider and self.provider.is_running:
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
                elif self._rotation_pending and not is_listening:
                    logger.info("Performing pending OpenAI session rotation.")
                    await self.stop_provider()
                    self._rotation_pending = False

            if self.provider and self.provider.get_type() != self.config.transcription.provider:
                logger.info(
                    f"Provider type mismatch ({self.provider.get_type()} != "
                    f"{self.config.transcription.provider}). Reconnecting..."
                )
                if not is_listening:
                    await self.stop_provider()

        # Fast path / task coalescing under a short lock only.
        async with self._state_lock:
            if self.provider and self.provider.is_running:
                return

            if self._connect_task and not self._connect_task.done():
                task = self._connect_task
            else:
                if self.provider is None:
                    provider = TranscriptionFactory.create(
                        self.config,
                        on_partial=self.on_partial,
                        on_final=self.on_final,
                        on_status=self.on_status,
                    )
                    self.provider = provider
                    self.audio_adapter = AudioAdapter(
                        capture_rate_hz=self.config.audio.capture_sample_rate,
                        provider_spec=provider.get_audio_spec(),
                        energy_threshold=self.config.audio.voice_activity_threshold,
                    )
                else:
                    provider = self.provider

                generation = self._generation
                task = asyncio.create_task(
                    self._connect_with_retry(provider, generation, is_listening),
                    name="connection-manager-connect",
                )
                self._connect_task = task

        # Await outside the lock so we don't block concurrent stops.
        await task

    async def _connect_with_retry(
        self, provider: BaseProvider, generation: int, is_listening: bool
    ):
        try:
            # Initial Backoff Application
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
            delay = self.config.audio.initial_backoff_seconds

            while current_attempt < retry_count:
                current_attempt += 1

                # Abort early if ownership has changed
                async with self._state_lock:
                    stale = self._generation != generation or self.provider is not provider
                if stale:
                    logger.debug("Connection aborted: Stale generation.")
                    return

                try:
                    logger.debug(
                        f"Starting provider {self.config.transcription.provider} "
                        f"(Attempt {current_attempt}/{retry_count})..."
                    )
                    async with asyncio.timeout(self.config.audio.connection_timeout_seconds):
                        await provider.start()
                        await provider.wait_for_ready()

                    # Commit success only if this attempt still owns the state
                    async with self._state_lock:
                        stale = self._generation != generation or self.provider is not provider
                        if not stale:
                            self._session_start_time = time.time()
                            self._rotation_pending = False
                            self._backoff_delay = self.config.audio.initial_backoff_seconds

                    if stale:
                        logger.info("Connected after invalidated. Cleaning up orphan provider.")
                        with contextlib.suppress(Exception):
                            await provider.stop()
                        return

                    logger.info("Connected successfully.")
                    if self.on_status:
                        self.on_status(STATUS_READY)

                    if not is_listening:
                        self.set_state(AppState.IDLE)

                    return  # Success - break out of the retry loop

                except asyncio.CancelledError:
                    # Required for graceful shutdown. Ensure provider is stopped.
                    logger.debug("Connect task cancelled. Stopping provider.")
                    with contextlib.suppress(Exception):
                        await provider.stop()
                    raise

                except (TimeoutError, Exception) as e:
                    is_last_attempt = current_attempt >= retry_count
                    error_msg = (
                        f"Connection attempt {current_attempt} failed: {type(e).__name__} - {e}"
                    )

                    # Partial failure cleanup before retry
                    with contextlib.suppress(Exception):
                        await provider.stop()

                    if is_last_attempt:
                        logger.error(f"{error_msg}. Giving up.")
                        if self.on_status:
                            self.on_status(STATUS_FAILED)
                    else:
                        logger.warning(f"{error_msg}. Retrying in {delay}s...")
                        if self.on_status:
                            self.on_status(STATUS_RETRYING)
                        await asyncio.sleep(delay)
                        delay = min(delay * 2, self.config.audio.max_backoff_seconds)

            # If we reach here, we've exhausted all retries
            self._last_fail_time = time.time()
            self._backoff_delay = min(
                self._backoff_delay * 2, self.config.audio.max_backoff_seconds
            )
            self.set_state(AppState.ERROR)

        finally:
            # Ensure we clear the task reference if we are the current task
            async with self._state_lock:
                if self._connect_task is asyncio.current_task():
                    self._connect_task = None

    async def stop_provider(self):
        """Stops the current provider and cleans up adapters safely."""
        # Detach global state first, under a short lock.
        async with self._state_lock:
            self._generation += 1
            provider = self.provider
            connect_task = self._connect_task
            adapter = self.audio_adapter

            self.provider = None
            self._connect_task = None
            self.audio_adapter = None

            if self._idle_timer_task:
                self._idle_timer_task.cancel()
                self._idle_timer_task = None

        # Cancel in-flight connect outside the lock.
        if connect_task and connect_task is not asyncio.current_task():
            connect_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await connect_task

        # Stop provider outside the lock.
        if provider:
            with contextlib.suppress(Exception):
                async with asyncio.timeout(self.config.audio.connection_timeout_seconds):
                    await provider.stop()

        # Cleanup audio adapter
        if adapter:
            adapter.close()

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
                    # Don't strictly check self.provider.is_running here because
                    # we want stop_provider() to cleanly increment the generation regardless.
                    logger.info(f"Closing warm connection after {timeout}s idle.")
                    await self.stop_provider()
                    break
                await asyncio.sleep(min(1.0, timeout - elapsed))
        except asyncio.CancelledError:
            pass

    async def shutdown(self):
        """Final cleanup of all connection resources."""
        await self.stop_provider()
