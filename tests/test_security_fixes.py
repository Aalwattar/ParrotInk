import pytest

from engine.app_types import EffectiveOpenAIConfig
from engine.config import Config, ConfigError
from engine.security import SecurityManager
from engine.transcription.openai_provider import OpenAIProvider


def test_url_trust_validation():
    """Verify that SecurityManager correctly identifies trusted domains."""
    assert SecurityManager.is_url_trusted("wss://api.openai.com/v1/realtime") is True
    assert SecurityManager.is_url_trusted("wss://streaming.assemblyai.com/v3/ws") is True
    assert SecurityManager.is_url_trusted("ws://localhost:8081") is True
    assert SecurityManager.is_url_trusted("ws://127.0.0.1:8081") is True

    assert SecurityManager.is_url_trusted("wss://malicious-proxy.com") is False
    assert SecurityManager.is_url_trusted("http://evil.com") is False
    assert SecurityManager.is_url_trusted("") is False


def test_config_update_validation_enforced():
    """Verify that update_and_save now enforces Pydantic validation."""
    config = Config()

    # Valid update
    config.update_and_save({"interaction": {"sounds": {"volume": 50}}}, blocking=True)
    assert config.interaction.sounds.volume == 50

    # Invalid update - wrong type (string instead of int for volume)
    with pytest.raises(ConfigError) as excinfo:
        config.update_and_save({"interaction": {"sounds": {"volume": "very_loud"}}}, blocking=True)

    # The message should mention validation failure
    assert "Update validation failed" in str(excinfo.value)
    # The original volume should remain unchanged
    assert config.interaction.sounds.volume == 50


@pytest.mark.asyncio
async def test_provider_refuses_untrusted_url():
    """Verify that OpenAIProvider refuses to connect to untrusted URLs in production mode."""
    eff_config = EffectiveOpenAIConfig(
        url="wss://untrusted.com",
        transcription_model="gpt-4o-mini-transcribe",
        prompt="",
        turn_detection_type="server_vad",
        vad_threshold=0.6,
        silence_duration_ms=500,
        prefix_padding_ms=300,
                    noise_reduction_type=None,
                                language="en",
                                trusted_domains=[],
                                stop_timeout=7.0,
                                is_test=False, # Production mode
                            )
                    
    provider = OpenAIProvider(
        api_key="sk-test",
        on_partial=lambda x: None,
        on_final=lambda x: None,
        effective_config=eff_config,
    )

    with pytest.raises(ConnectionError) as excinfo:
        await provider.start()

    assert "Untrusted transcription endpoint" in str(excinfo.value)


@pytest.mark.asyncio
async def test_provider_allows_untrusted_url_in_test_mode(mocker):
    """Verify that OpenAIProvider allows untrusted URLs when is_test is True."""
    eff_config = EffectiveOpenAIConfig(
        url="ws://untrusted.com",  # In real life, this would be a mock server
        transcription_model="gpt-4o-mini-transcribe",
        prompt="",
        turn_detection_type="server_vad",
        vad_threshold=0.6,
        silence_duration_ms=500,
        prefix_padding_ms=300,
                    noise_reduction_type=None,
                                language="en",
                                trusted_domains=[],
                                stop_timeout=7.0,
                                is_test=True, # Test mode
                            )
                    
    # Mock websockets.connect to prevent actual network calls
    mock_connect = mocker.patch("websockets.connect", side_effect=Exception("Mock connected"))

    provider = OpenAIProvider(
        api_key="sk-test",
        on_partial=lambda x: None,
        on_final=lambda x: None,
        effective_config=eff_config,
    )

    # In test mode, it should proceed to call websockets.connect (which we mocked to fail)
    with pytest.raises(Exception) as excinfo:
        await provider.start()

    assert "Mock connected" in str(excinfo.value)
    # Verify connect was called WITHOUT headers
    mock_connect.assert_called_once_with("ws://untrusted.com", additional_headers=None)


def test_log_pii_redaction():
    """Verify that SanitizingFormatter redacts transcription text."""
    import logging

    from engine.logging import SanitizingFormatter

    formatter = SanitizingFormatter("%(message)s")

    # Case 1: OpenAI structured log
    msg1 = 'OpenAI Final Segment: {"transcript": "My secret password is 12345"}'
    record1 = logging.LogRecord("test", logging.DEBUG, "path", 1, msg1, None, None)
    formatted1 = formatter.format(record1)
    # Should keep "My secret " (9 chars + space) and then redact
    assert '{"transcript": "My secret <PII_REDACTED>"}' in formatted1
    assert "12345" not in formatted1

    # Case 2: AssemblyAI structured log
    msg2 = 'AssemblyAI Final: {"text": "Patient has a history of heart disease"}'
    record2 = logging.LogRecord("test", logging.DEBUG, "path", 1, msg2, None, None)
    formatted2 = formatter.format(record2)
    assert '{"text": "Patient ha<PII_REDACTED>"}' in formatted2
    assert "heart disease" not in formatted2


def test_log_path_safety():
    """Verify that is_path_safe correctly identifies dangerous paths."""
    import os

    from engine.logging import is_path_safe

    # Standard safe paths
    assert is_path_safe("parrotink.log") is True  # Relative to CWD
    assert is_path_safe(os.path.join(os.environ.get("TEMP", "."), "test.log")) is True

    # Dangerous paths
    assert is_path_safe("C:/Windows/System32/drivers/etc/hosts") is False
    # Path traversal
    assert is_path_safe("../../../../../Windows/win.ini") is False
