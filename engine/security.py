import os
from typing import Optional

import keyring

from .logging import get_logger

logger = get_logger("Security")


class SecurityManager:
    """Manages secure storage and resolution of API keys."""

    SERVICE_NAME = "parrotink"
    LEGACY_SERVICE_NAME = "voice2text"

    @classmethod
    def get_key(cls, account_name: str) -> Optional[str]:
        """
        Resolves an API key using the precedence:
        1. Windows Credential Manager (keyring) - Current Name
        2. Windows Credential Manager (keyring) - Legacy Name
        3. Environment Variables (UPPER_CASE)
        """
        # 1. Keyring - Current
        try:
            key = keyring.get_password(cls.SERVICE_NAME, account_name)
            if key:
                return key
        except Exception as e:
            print(f"Warning: Keyring lookup failed for {account_name} ({cls.SERVICE_NAME}): {e}")

        # 2. Keyring - Legacy
        try:
            key = keyring.get_password(cls.LEGACY_SERVICE_NAME, account_name)
            if key:
                # Proactively migrate to new service name
                logger.info(
                    f"Migrating key '{account_name}' from "
                    f"{cls.LEGACY_SERVICE_NAME} to {cls.SERVICE_NAME}"
                )
                cls.set_key(account_name, key)
                return key
        except Exception:
            pass

        # 3. Environment Variable
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
