import asyncio
import numpy as np
from engine.transcription.openai_provider import OpenAIProvider
from engine.transcription.assemblyai_provider import AssemblyAIProvider

async def test_openai():
    print("\n--- Testing OpenAI Provider ---")
    final_text = []
    def on_final(text):
        print(f"OpenAI Final: {text}")
        final_text.append(text)

    provider = OpenAIProvider(api_key="mock", on_partial=lambda x: None, on_final=on_final)
    provider.url = "ws://127.0.0.1:8081"
    
    await provider.start()
    await provider.send_audio(np.zeros(1024, dtype=np.float32))
    await asyncio.sleep(1)
    await provider.stop()
    
    if "Hello from mock OpenAI!" not in final_text:
        raise Exception("OpenAI verification failed")

async def test_assemblyai():
    print("\n--- Testing AssemblyAI Provider ---")
    final_text = []
    def on_final(text):
        print(f"AssemblyAI Final: {text}")
        final_text.append(text)

    provider = AssemblyAIProvider(api_key="mock", on_partial=lambda x: print(f"AAI Partial: {x}"), on_final=on_final)
    provider.url = "ws://127.0.0.1:8082"
    
    await provider.start()
    await provider.send_audio(np.zeros(1024, dtype=np.float32))
    await asyncio.sleep(1)
    await provider.stop()
    
    if "Hello from mock AssemblyAI!" not in final_text:
        raise Exception("AssemblyAI verification failed")

async def main():
    try:
        await test_openai()
        await test_assemblyai()
        print("\nVerification SUCCESS")
    except Exception as e:
        print(f"\nVerification FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(main())