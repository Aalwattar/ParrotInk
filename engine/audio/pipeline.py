import asyncio
from typing import Optional

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
        self.streamer.start(loop=loop)
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
        chunks_sent = 0
        try:
            async for chunk, capture_time in self.streamer.async_generator():
                # Strict gating: only process if we are still marked as running
                if not self._is_running:
                    continue

                processed = adapter.process(chunk)
                await provider.send_audio(processed, capture_time)

                chunks_sent += 1
                if chunks_sent % 100 == 0:
                    logger.debug(f"Pipeline heartbeat: sent {chunks_sent} chunks")
        except Exception as e:
            # We don't want to crash the whole app if the pipe fails,
            # but we should log it prominently.
            if self._is_running:
                logger.error(f"Critical error in audio pipeline: {e}")
                logger.debug("Pipeline traceback: ", exc_info=True)
