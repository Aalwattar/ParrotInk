from __future__ import annotations

import asyncio
import inspect
import json
import time
import wave
from pathlib import Path
from typing import Optional

from engine.app_types import TranscriptionError
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

    def on_partial(self, text: str) -> None:
        if self.time_to_first_partial is None and text.strip():
            self.time_to_first_partial = time.time() - self.start_time
            logger.info(f"First partial received at {self.time_to_first_partial:.2f}s")

    def on_final(self, text: str) -> None:
        if self.time_to_first_final is None and text.strip():
            self.time_to_first_final = time.time() - self.start_time
            logger.info(f"First final received at {self.time_to_first_final:.2f}s")

        if text.strip():
            if self.final_text:
                self.final_text += " " + text.strip()
            else:
                self.final_text = text.strip()

            # Signal that we have a result
            self.finished_event.set()

    async def run(self) -> None:
        configure_logging(
            self.config, verbose_count=self.cli_args.verbose, quiet=self.cli_args.quiet
        )

        if not self.audio_path.exists():
            self._fail("invalid_wav", f"File not found: {self.audio_path}")
            return

        replayer = WavReplayer(self.audio_path, chunk_ms=self.config.audio.chunk_ms)

        # Get sample rate from replayer to ensure correct resampling
        try:
            with wave.open(str(self.audio_path), "rb") as wr:
                wav_sample_rate = wr.getframerate()
        except Exception as e:
            self._fail("invalid_wav", f"Could not read WAV header: {e}")
            return

        logger.info(f"Connecting to {self.provider_name}...")
        try:
            # Force the selected provider in config for the factory
            self.config.transcription.provider = self.provider_name
            if getattr(self.cli_args, "model", None):
                from engine.transcription.catalog import model_config_update

                update = model_config_update(self.provider_name, self.cli_args.model)
                provider_config = update["providers"][self.provider_name]["core"]
                for field, value in provider_config.items():
                    setattr(getattr(self.config.providers, self.provider_name).core, field, value)
            provider = TranscriptionFactory.create(
                self.config,
                on_partial=self.on_partial,
                on_final=self.on_final,
                on_error=self.on_error,
            )
            adapter = AudioAdapter(
                capture_rate_hz=wav_sample_rate,
                provider_spec=provider.get_audio_spec(),
            )
        except Exception as e:
            self._fail("config_error", str(e))
            return

        started = False
        try:
            async with asyncio.timeout(self.cli_args.timeout_seconds):
                await provider.start()
                await self._call_hook(provider, "wait_for_ready")
                started = True
                self.start_time = time.time()
                logger.info("Starting audio replay...")
                try:
                    async for chunk, capture_time in replayer.async_generator():
                        if self.error:
                            break
                        processed = adapter.process(chunk)
                        await self._call_hook(
                            provider,
                            "notify_voice_activity",
                            bool(adapter.voice_active),
                            capture_time,
                        )
                        await provider.send_audio(processed, capture_time)
                    logger.info("Audio replay finished.")
                except Exception as e:
                    self._fail("replayer_error", str(e))
                    return
                if self.error:
                    return
                # Provider finalization drains every committed turn. An early final
                # measures latency; it must never truncate the rest of the recording.
                has_finish_hook = await asyncio.wait_for(
                    self._call_hook(provider, "finish_utterance"), timeout=5.0
                )
                if not has_finish_hook:
                    try:
                        await asyncio.wait_for(self.finished_event.wait(), timeout=5.0)
                    except TimeoutError:
                        logger.warning("No final transcript received after audio replay.")
        except asyncio.TimeoutError:
            self._fail("timeout", f"Evaluation timed out after {self.cli_args.timeout_seconds}s")
            return
        except Exception as e:
            self._fail("ws_error" if started else "provider_auth", str(e))
            return
        finally:
            try:
                await provider.stop()
            except Exception as e:
                self._fail("ws_error", f"Could not stop the provider: {e}")
            finally:
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
        if self.error:
            return
        self.error = {"status": "error", "error_code": code, "message": message}
        print(json.dumps(self.error))
        self.finished_event.set()

    def on_error(self, error: TranscriptionError):
        self._fail("ws_error", f"{error.title}: {error.message}")

    @staticmethod
    async def _call_hook(provider, name: str, *args) -> bool:
        """Allow older evaluation doubles that lack the newer lifecycle hooks."""
        hook = getattr(provider, name, None)
        if not callable(hook):
            return False
        result = hook(*args)
        if inspect.isawaitable(result):
            await result
        return True


async def main_eval(cli_args):
    coordinator = EvalCoordinator(cli_args)
    await coordinator.run()
