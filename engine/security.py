import os
from typing import Optional

import keyring

from .logging import get_logger

logger = get_logger("Security")


class SecurityManager:
    """Manages secure storage and resolution of API keys."""

    SERVICE_NAME = "parrotink"

    @classmethod
    def get_key(cls, account_name: str) -> Optional[str]:
        """
        Resolves an API key using the precedence:
        1. Windows Credential Manager (keyring)
        2. Environment Variables (UPPER_CASE)
        """
        # 1. Keyring
        try:
            key = keyring.get_password(cls.SERVICE_NAME, account_name)
            if key:
                return key
        except Exception as e:
            print(f"Warning: Keyring lookup failed for {account_name}: {e}")

        # 2. Environment Variable
        env_var = account_name.upper()
        return os.environ.get(env_var)

    @classmethod
    def set_key(cls, account_name: str, key: str) -> None:
        """Saves an API key to the Windows Credential Manager."""
        if not key:
            # If key is empty, delete it
            try:
                keyring.delete_password(cls.SERVICE_NAME, account_name)
            except keyring.errors.PasswordDeleteError:
                pass  # Already deleted
            return

        keyring.set_password(cls.SERVICE_NAME, account_name, key)

    @classmethod
    def is_url_trusted(cls, url: str) -> bool:
        """
        Validates if a URL belongs to a trusted transcription provider domain.
        Used to prevent credential exfiltration to malicious custom endpoints.
        
        This check is strictly hardcoded in engine/constants.py to prevent
        manipulation via the local config file.
        """
        if not url:
            return False

        try:
            from urllib.parse import urlparse

            from engine.constants import TRUSTED_DOMAINS

            parsed = urlparse(url)
            # hostname handles cases with ports (e.g. localhost:8081)
            host = (parsed.hostname or "").lower()

            return host in TRUSTED_DOMAINS
        except Exception:
            return False
