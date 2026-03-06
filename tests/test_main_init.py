import pytest


@pytest.mark.asyncio
async def test_coordinator_initialization(coordinator):
    assert (
        coordinator.config.transcription.provider == "openai"
        or coordinator.config.transcription.provider == "assemblyai"
    )


@pytest.mark.asyncio
async def test_coordinator_basic_state(coordinator):
    assert coordinator.state.name == "IDLE"
