import pytest
from engine.constants import TRUSTED_DOMAINS

def test_trusted_domains_presence():
    """Verify that TRUSTED_DOMAINS contains the required baseline endpoints."""
    expected = {
        "api.openai.com",
        "streaming.assemblyai.com",
        "streaming.eu.assemblyai.com",
        "localhost",
        "127.0.0.1",
    }
    for domain in expected:
        assert domain in TRUSTED_DOMAINS

def test_trusted_domains_is_set():
    """Verify that TRUSTED_DOMAINS is a set (for O(1) lookup)."""
    assert isinstance(TRUSTED_DOMAINS, (set, frozenset))
