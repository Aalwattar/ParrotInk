from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.eval_main import EvalCoordinator


@pytest.mark.asyncio
async def test_eval_coordinator_accumulation():
    args = MagicMock(spec=["provider", "audio", "config", "verbose", "quiet", "timeout_seconds"])
    args.provider = "mock"
    args.audio = "tests/sample.wav"
    args.config = None
    args.verbose = 0
    args.quiet = True
    args.timeout_seconds = 10

    # Mock dependencies
    with (
        patch("engine.eval_main.load_config"),
        patch("engine.eval_main.TranscriptionFactory") as mock_factory,
        patch("engine.eval_main.AudioAdapter"),
        patch("engine.eval_main.WavReplayer"),
        patch("wave.open") as mock_wave_open,
    ):
        # Mock wave.open to return a sample rate
        mock_wave = MagicMock()
        mock_wave.getframerate.return_value = 16000
        mock_wave_open.return_value.__enter__.return_value = mock_wave

        # Mock provider
        mock_provider = AsyncMock()
        mock_provider.get_audio_spec.return_value = MagicMock()
        mock_factory.create.return_value = mock_provider

        coordinator = EvalCoordinator(args)

        # Simulate callbacks
        coordinator.on_final("Hello")
        coordinator.on_final("World")

        assert coordinator.final_text == "Hello World"
        assert coordinator.time_to_first_final is not None


@pytest.mark.asyncio
async def test_eval_coordinator_first_partial():
    args = MagicMock(spec=["provider", "audio", "config", "verbose", "quiet", "timeout_seconds"])
    args.provider = "mock"
    args.audio = "tests/sample.wav"
    args.config = None
    coordinator = EvalCoordinator(args)

    coordinator.on_partial("Hel")
    first_time = coordinator.time_to_first_partial
    assert first_time is not None

    coordinator.on_partial("Hello")
    assert coordinator.time_to_first_partial == first_time
