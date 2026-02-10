import os
import keyring
from typing import Optional

try:
    import tkinter as tk
    from tkinter import simpledialog
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

class SecurityManager:
    """Manages secure storage and resolution of API keys."""
    
    SERVICE_NAME = "voice2text"
    
    @classmethod
    def get_key(cls, account_name: str) -> Optional[str]:
        """
        Resolves an API key using the precedence:
        1. Windows Credential Manager (keyring)
        2. Environment Variables (UPPER_CASE)
        """
        # 1. Keyring
        key = keyring.get_password(cls.SERVICE_NAME, account_name)
        if key:
            return key
            
        # 2. Environment Variable
        env_var = account_name.upper()
        return os.environ.get(env_var)

    @classmethod
    def set_key(cls, account_name: str, key: str) -> None:
        """Saves an API key to the Windows Credential Manager."""
        keyring.set_password(cls.SERVICE_NAME, account_name, key)

class CredentialDialog:
    """Helper to show a password-masked input dialog."""
    
    @staticmethod
    def ask_key(provider_name: str) -> Optional[str]:
        """Shows a tkinter dialog to prompt for an API key."""
        if not HAS_TKINTER:
            print(f"Error: tkinter is not installed. Cannot show dialog for {provider_name}.")
            return None
            
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Ensure dialog is on top
        root.attributes("-topmost", True)
        
        key = simpledialog.askstring(
            f"Set {provider_name} Key",
            f"Enter your {provider_name} API Key:",
            show="*",
            parent=root
        )
        
        root.destroy()
        return key
