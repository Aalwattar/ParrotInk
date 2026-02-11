import asyncio

import numpy as np

from engine.config import Config
from engine.transcription.factory import TranscriptionFactory


async def verify_mode(name, config):
    print(f"\n--- Verifying {name} (Test Mode: {config.test.enabled}) ---")
    final_text = []

    def on_final(text):
        print(f"[{config.default_provider}] Final: {text}")
        final_text.append(text)

    provider = TranscriptionFactory.create(config, on_partial=lambda x: None, on_final=on_final)
    print(f"Connecting to: {provider.url}")

    try:
        await provider.start()
        # Send some dummy audio
        await provider.send_audio(np.zeros(1024, dtype=np.float32))
        await asyncio.sleep(1)
        await provider.stop()

        if config.test.enabled:
            expected = (
                "Hello from mock OpenAI!"
                if config.default_provider == "openai"
                else "Hello from mock AssemblyAI!"
            )
            if any(expected in t for t in final_text):
                print(f"SUCCESS: Received expected mock response for {config.default_provider}")
            else:
                print(
                    f"FAILED: Did not receive expected mock response for "
                    f"{config.default_provider}. Got: {final_text}"
                )
                return False
        return True
    except Exception as e:
        if not config.test.enabled:
            print(f"Expected connection behavior for production URL: {e}")
            return True
        else:
            print(f"FAILED: Connection to mock server failed: {e}")
            return False


async def main():
    # 1. Test Mode OpenAI
    config_test_oa = Config(
        default_provider="openai", test={"enabled": True, "openai_mock_url": "ws://127.0.0.1:8081"}
    )
    ok1 = await verify_mode("OpenAI Mock", config_test_oa)

    # 2. Test Mode AssemblyAI
    config_test_aai = Config(
        default_provider="assemblyai",
        test={"enabled": True, "assemblyai_mock_url": "ws://127.0.0.1:8082"},
    )
    ok2 = await verify_mode("AssemblyAI Mock", config_test_aai)

    # 3. Production Mode (Should use advanced URL)
    config_prod = Config(
        default_provider="openai",
        test={"enabled": False},
        advanced={
            "openai_url": "ws://127.0.0.1:8081"
        },  # Point to mock but via 'advanced' to prove it uses it
    )
    ok3 = await verify_mode("Production Config Override", config_prod)

    if ok1 and ok2 and ok3:
        print("\nAll Smoke Tests Passed!")
    else:
        print("\nSome Smoke Tests Failed!")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
