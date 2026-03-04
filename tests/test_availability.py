from engine.config import Config
from main import AppCoordinator


def test_availability_test_mode():
    config = Config(test={"enabled": True})
    coordinator = AppCoordinator(config)

    availability = coordinator.get_provider_availability()
    assert availability["openai"] is True
    assert availability["assemblyai"] is True


def test_availability_production_missing_keys(mocker):
    config = Config(test={"enabled": False})
    coordinator = AppCoordinator(config)

    # Mock SecurityManager to return None for both
    mocker.patch("engine.security.SecurityManager.get_key", return_value=None)

    availability = coordinator.get_provider_availability()
    assert availability["openai"] is False
    assert availability["assemblyai"] is False


def test_availability_production_partial_keys(mocker):
    config = Config(test={"enabled": False})
    coordinator = AppCoordinator(config)

    # Mock SecurityManager: openai has key, assemblyai doesn't
    def mock_get_key(account):
        if account == "openai_api_key":
            return "sk-valid-key"
        return None

    mocker.patch("engine.security.SecurityManager.get_key", side_effect=mock_get_key)

    availability = coordinator.get_provider_availability()
    assert availability["openai"] is True
    assert availability["assemblyai"] is False
