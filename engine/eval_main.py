from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Optional

from engine.audio.adapter import AudioAdapter
from engine.audio.replay import WavReplayer
from engine.config import load_config
from engine.logging import configure_logging, get_logger
from engine.transcription.factory import TranscriptionFactory

logger = get_logger("Eval")


class EvalCoordinator:
    def __init__(self, cli_args):
        self.cli_args = cli_args
        self.config = (
            load_config(cli_args.config)
            if hasattr(cli_args, "config") and cli_args.config
            else load_config()
        )

        # Override chunk_ms if provided
        if hasattr(cli_args, "chunk_ms") and cli_args.chunk_ms:
            self.config.audio.chunk_ms = cli_args.chunk_ms

        self.provider_name = cli_args.provider
        self.audio_path = Path(cli_args.audio)

        self.final_text = ""
        self.time_to_first_partial: Optional[float] = None
        self.time_to_first_final: Optional[float] = None
        self.start_time = 0.0

        self.loop = asyncio.get_running_loop()
        self.finished_event = asyncio.Event()
        self.error: Optional[dict] = None

    def on_partial(self, text: str):
        if self.time_to_first_partial is None and text.strip():
            self.time_to_first_partial = time.time() - self.start_time
            logger.info(f"First partial received at {self.time_to_first_partial:.2f}s")

    def on_final(self, text: str):
        if self.time_to_first_final is None and text.strip():
            self.time_to_first_final = time.time() - self.start_time
            logger.info(f"First final received at {self.time_to_first_final:.2f}s")

        self.final_text = text.strip()
        # For evaluation, we assume one WAV = one final result.
        # We signal finish when we get a non-empty final result.
        if self.final_text:
            self.finished_event.set()

    async def run(self):
        configure_logging(
            self.config, verbose_count=self.cli_args.verbose, quiet=self.cli_args.quiet
        )

        if not self.audio_path.exists():
            self._fail("invalid_wav", f"File not found: {self.audio_path}")
            return

        # Initialize provider
        try:
            # Force the selected provider in config for the factory
            self.config.default_provider = self.provider_name
            provider = TranscriptionFactory.create(
                self.config, on_partial=self.on_partial, on_final=self.on_final
            )
            adapter = AudioAdapter(
                capture_rate_hz=self.config.audio.capture_sample_rate,
                provider_spec=provider.get_audio_spec(),
            )
        except Exception as e:
            self._fail("config_error", str(e))
            return

        replayer = WavReplayer(self.audio_path, chunk_ms=self.config.audio.chunk_ms)

        logger.info(f"Connecting to {self.provider_name}...")
        try:
            await provider.start()
        except Exception as e:
            self._fail("provider_auth", str(e))
            return

        self.start_time = time.time()
        logger.info("Starting audio replay...")

        # Run replayer and provider in parallel
        try:
            async with asyncio.timeout(self.cli_args.timeout_seconds):
                # Task 1: Replay audio
                async def stream_audio():
                    try:
                        async for chunk, _ in replayer.async_generator():
                            processed = adapter.process(chunk)
                            await provider.send_audio(processed, time.time())
                        logger.info("Audio replay finished.")
                    except Exception as e:
                        logger.error(f"Replayer error: {e}")
                        self._fail("replayer_error", str(e))

                audio_task = asyncio.create_task(stream_audio())

                # Task 2: Wait for finalization
                await self.finished_event.wait()
                audio_task.cancel()
        except asyncio.TimeoutError:
            self._fail("timeout", f"Evaluation timed out after {self.cli_args.timeout_seconds}s")
            return
        except Exception as e:
            self._fail("ws_error", str(e))
            return
        finally:
            await provider.stop()
            adapter.close()

        # Success Output
        if not self.error:
            result = {
                "status": "ok",
                "provider": self.provider_name,
                "audio_file": str(self.audio_path),
                "config_file": str(getattr(self.cli_args, "config", "default")),
                "chunk_ms": self.config.audio.chunk_ms,
                "realtime": True,
                "time_to_first_partial_s": self.time_to_first_partial,
                "time_to_first_final_s": self.time_to_first_final,
                "final_text": self.final_text,
            }
            print(json.dumps(result))

    def _fail(self, code: str, message: str):
        self.error = {"status": "error", "error_code": code, "message": message}
        print(json.dumps(self.error))
        self.finished_event.set()


async def main_eval(cli_args):
    coordinator = EvalCoordinator(cli_args)
    await coordinator.run()
