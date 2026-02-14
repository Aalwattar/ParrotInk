import asyncio
import sys

from engine.config import Config
from engine.ui_bridge import UIBridge, UIEvent
from main import AppCoordinator


async def verify_mock_transcription():
    """Verify that mock transcription works end-to-end in test mode."""
    print("Starting Mock Transcription Verification...")

    config = Config()
    config.test.enabled = True
    config.transcription.provider = "openai"

    bridge = UIBridge()
    coordinator = AppCoordinator(config, bridge)
    coordinator.loop = asyncio.get_running_loop()

    final_text = ""

    def on_event(event):
        nonlocal final_text
        msg_type, data = event
        if msg_type == UIEvent.UPDATE_FINAL_TEXT:
            final_text = data
            print(f"[UI] Final Text Received: {data}")

    # Patch bridge to intercept events
    bridge.put_event = on_event

    print(f"Using provider: {config.transcription.provider}")

    # Start listening
    await coordinator.start_listening()

    # Wait for a bit to receive mock events
    await asyncio.sleep(2.0)

    # Stop listening
    await coordinator.stop_listening()

    if final_text:
        print(f"SUCCESS: Received expected mock response for {config.transcription.provider}")
    else:
        print(f"FAILURE: Did not receive mock response for {config.transcription.provider}")
        sys.exit(1)

    # Now test AssemblyAI mock
    config.transcription.provider = "assemblyai"
    final_text = ""
    print(f"Using provider: {config.transcription.provider}")

    await coordinator.start_listening()
    await asyncio.sleep(2.0)
    await coordinator.stop_listening()

    if final_text:
        print(f"SUCCESS: Received expected mock response for {config.transcription.provider}")
    else:
        print(f"FAILURE: Did not receive mock response for {config.transcription.provider}")
        sys.exit(1)

    await coordinator.shutdown()
    print("Verification Complete.")


if __name__ == "__main__":
    asyncio.run(verify_mock_transcription())
