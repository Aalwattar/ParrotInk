import asyncio

from engine.audio import AudioStreamer


async def main():
    streamer = AudioStreamer()
    streamer.start()
    print("Recording 3 seconds of audio data...")
    count = 0
    try:
        async for chunk, _timestamp in streamer.async_generator():
            count += 1
            if count > 30:  # ~3 seconds
                break
            print(f"Captured chunk {count}, max amplitude: {chunk.max():.4f}")
    finally:
        streamer.stop()


if __name__ == "__main__":
    asyncio.run(main())
