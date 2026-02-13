import os
import sys
import traceback

import httpx
from openai import OpenAI

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.golden_tools.auth_utils import get_openai_key


def test_connectivity():
    try:
        api_key = get_openai_key()
    except Exception as e:
        print(f"Failed to get API key: {e}")
        return

    print("Testing connectivity to OpenAI...")

    # 1. Test basic DNS/HTTPS with httpx
    print("\n--- Step 1: Basic HTTPS check with httpx ---")
    try:
        with httpx.Client() as client:
            response = client.get(
                "https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {api_key}"}
            )
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                print("Successfully fetched models list via httpx.")
            else:
                print(f"Error response: {response.text}")
    except Exception as e:
        print(f"httpx connection failed: {e}")
        traceback.print_exc()

    # 2. Test with OpenAI library
    print("\n--- Step 2: OpenAI Library check ---")
    try:
        client = OpenAI(api_key=api_key, timeout=20.0)
        # Just list models to test connection
        models = client.models.list()
        print("Successfully listed models via OpenAI library.")

        # Check if gpt-4o-transcribe is in the list
        model_ids = [m.id for m in models.data]
        if "gpt-4o-transcribe" in model_ids:
            print("Found 'gpt-4o-transcribe' in available models.")
        elif "whisper-1" in model_ids:
            print("Found 'whisper-1', but 'gpt-4o-transcribe' is missing.")
        else:
            print(f"Available models (first 5): {model_ids[:5]}")

    except Exception as e:
        print(f"OpenAI library connection failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    test_connectivity()
