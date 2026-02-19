import pytest
from engine.config import Config
from engine.security import SecurityManager

def test_custom_trusted_domain_via_config():
    """Verify that a domain added via config is trusted by SecurityManager."""
    config = Config()
    custom_domain = "my-custom-proxy.internal"
    
    # Pre-condition: Domain is NOT trusted
    assert SecurityManager.is_url_trusted(f"wss://{custom_domain}") is False
    
    # Update config with custom domain
    config.update_and_save({"security": {"trusted_domains": [custom_domain]}}, blocking=True)
    
    # Verify resolution
    from engine.config_resolver import resolve_effective_config
    eff = resolve_effective_config(config)
    assert custom_domain in eff.openai.trusted_domains
    assert custom_domain in eff.assemblyai.trusted_domains

    # ASSERT: Domain IS now trusted when extra_trusted is provided
    assert SecurityManager.is_url_trusted(
        f"wss://{custom_domain}",
        extra_trusted=config.security.trusted_domains
    ) is True
