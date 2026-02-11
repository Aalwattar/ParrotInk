import os

from engine.security import SecurityManager


def test_get_key_from_keyring(mocker):
    """Should return key from keyring if available."""
    mock_keyring = mocker.patch("keyring.get_password")
    mock_keyring.return_value = "keyring-secret"

    key = SecurityManager.get_key("openai_api_key")

    assert key == "keyring-secret"
    mock_keyring.assert_called_once_with("voice2text", "openai_api_key")


def test_get_key_fallback_to_env(mocker):
    """Should return key from environment if not in keyring."""
    mock_keyring = mocker.patch("keyring.get_password")
    mock_keyring.return_value = None

    mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "env-secret"})

    key = SecurityManager.get_key("openai_api_key")

    assert key == "env-secret"


def test_get_key_not_found(mocker):
    """Should return None if key is nowhere to be found."""
    mocker.patch("keyring.get_password", return_value=None)
    mocker.patch.dict(os.environ, {}, clear=True)

    key = SecurityManager.get_key("non_existent")
    assert key is None


def test_set_key(mocker):
    """Should save key to keyring."""
    mock_keyring = mocker.patch("keyring.set_password")

    SecurityManager.set_key("openai_api_key", "new-secret")

    mock_keyring.assert_called_once_with("voice2text", "openai_api_key", "new-secret")
