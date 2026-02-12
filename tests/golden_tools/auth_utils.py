import os
import sys

# Add project root to sys.path to import engine modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from engine.security import SecurityManager


def get_openai_key() -> str:
    """Retrieve OpenAI API key from Windows Credential Manager."""
    key = SecurityManager.get_key("openai_api_key")
    if not key:
        print("Error: OpenAI API key not found in Credential Manager.")
        sys.exit(1)
    return key

def get_assemblyai_key() -> str:
    """Retrieve AssemblyAI API key from Windows Credential Manager."""
    key = SecurityManager.get_key("assemblyai_api_key")
    if not key:
        print("Error: AssemblyAI API key not found in Credential Manager.")
        sys.exit(1)
    return key
