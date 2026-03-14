import asyncio
from typing import Callable, Optional

from engine.audio.adapter import AudioAdapter
from engine.audio.streamer import AudioStreamer
from engine.logging import get_logger
from engine.transcription.base import BaseProvider

logger = get_logger("AudioPipeline")


class AudioPipeline:
    """
    Orchestrates the flow of audio from the capture streamer
    through the adapter and into the transcription provider.
    """

    def __init__(self, streamer: AudioStreamer):
        self.streamer = streamer
        self._audio_task: Optional[asyncio.Task] = None
        self._is_running = False
        self.on_voice_activity: Optional[Callable[[bool], None]] = None

    @property
    def is_active(self) -> bool:
        return self._is_running

    async def start(
        self, adapter: AudioAdapter, provider: BaseProvider, loop: asyncio.AbstractEventLoop
    ):
        """Starts the audio capture and the asynchronous processing pipe."""
        if self._is_running:
            return

        self._is_running = True
        await self.streamer.start(loop=loop)

        # Guard against zero sample rate just in case, though streamer handles it
        if getattr(self.streamer, "sample_rate", 16000) != adapter.capture_rate_hz:
            logger.info(
                f"Streamer fallback changed sample rate to {self.streamer.sample_rate}. "
                "Updating adapter."
            )
            adapter.update_capture_rate(self.streamer.sample_rate)

        self._audio_task = asyncio.create_task(self._run_pipe(adapter, provider))
        logger.debug("Audio pipeline started.")

    async def stop(self):
        """Stops capture and cancels the processing pipe."""
        self._is_running = False
        self.streamer.stop()

        if self._audio_task:
            self._audio_task.cancel()
            try:
                await self._audio_task
            except asyncio.CancelledError:
                pass
            self._audio_task = None

        logger.debug("Audio pipeline stopped.")

    async def _run_pipe(self, adapter: AudioAdapter, provider: BaseProvider):
        """Internal loop that pulls from streamer and sends to provider."""
        last_voice_active = False
        try:
            async for chunk, capture_time in self.streamer.async_generator():
                # Strict gating: only process if we are still marked as running
                if not self._is_running:
                    continue

                # Safely log status changes if they happened in the driver thread
                if self.streamer.last_status:
                    logger.warning(f"Audio status warning: {self.streamer.last_status}")
                    self.streamer.last_status = None

                processed = adapter.process(chunk)

                # Update Voice Activity Signal (Debounced for the HUD)
                if self.on_voice_activity and adapter.voice_active != last_voice_active:
                    self.on_voice_activity(adapter.voice_active)
                    last_voice_active = adapter.voice_active

                await provider.send_audio(processed, capture_time)

                # Check if provider has crashed/stopped due to network failure
                if not provider.is_running and self._is_running:
                    logger.error(f"Provider {provider.get_type()} stopped unexpectedly.")
                    break

        except Exception as e:
            # We don't want to crash the whole app if the pipe fails,

            # but we should log it prominently.
            if self._is_running:
                logger.error(f"Critical error in audio pipeline: {e}")
                logger.debug("Pipeline traceback: ", exc_info=True)
