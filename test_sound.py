from engine.audio import AudioStreamer

streamer = AudioStreamer()
streamer.start()
print("Recording 3 seconds of audio data...")
count = 0
for chunk in streamer.generator():
    count += 1
    if count > 30:  # ~3 seconds
        break
    print(f"Captured chunk {count}, max amplitude: {chunk.max()}")
streamer.stop()
