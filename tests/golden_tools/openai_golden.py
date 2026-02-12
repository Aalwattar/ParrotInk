import argparse
import json
import os
import sys
import wave
from datetime import datetime

from openai import OpenAI

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from tests.golden_tools.auth_utils import get_openai_key

# OpenAI limit is 25MB. We use 20MB for safety.
CHUNK_SIZE_BYTES = 20 * 1024 * 1024

def split_wav(file_path: str) -> list[str]:
    """Splits a WAV file into chunks under the size limit if necessary."""
    file_size = os.path.getsize(file_path)
    if file_size <= CHUNK_SIZE_BYTES:
        return [file_path]

    print(f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds limit. Chunking...")
    chunks = []
    with wave.open(file_path, "rb") as wav:
        params = wav.getparams()
        frames_per_chunk = CHUNK_SIZE_BYTES // (params.nchannels * params.sampwidth)

        total_frames = wav.getnframes()
        current_frame = 0
        chunk_idx = 0

        while current_frame < total_frames:
            chunk_filename = f"{file_path}.chunk{chunk_idx}.wav"
            frames_to_read = min(frames_per_chunk, total_frames - current_frame)

            with wave.open(chunk_filename, 'wb') as chunk_wav:
                chunk_wav.setparams(params)
                chunk_wav.writeframes(wav.readframes(frames_to_read))

            chunks.append(chunk_filename)
            current_frame += frames_to_read
            chunk_idx += 1

    return chunks

def transcribe_openai(audio_path: str, format: str = "text"):
    client = OpenAI(api_key=get_openai_key())

    chunks = split_wav(audio_path)
    full_text = []

    # We use the new flagship gpt-4o-transcribe model for the Golden Standard
    model = "gpt-4o-transcribe"

    for chunk in chunks:
        with open(chunk, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                # gpt-4o-transcribe currently only supports text or json (not verbose_json)
                response_format="text" if format == "text" else "json"
            )
            # Handle different return types based on response_format
            if isinstance(transcript, str):
                full_text.append(transcript)
            else:
                # In JSON mode, transcript is an object with a .text attribute
                full_text.append(transcript.text)

    # Cleanup chunks if we created them
    if len(chunks) > 1:
        for chunk in chunks:
            if chunk != audio_path:
                os.remove(chunk)

    final_text = " ".join(full_text).strip()

    if format == "json":
        output = {
            "status": "ok",
            "provider": "openai",
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "audio_file": audio_path,
            "api_config": {
                "model": model,
                "response_format": "json"
            },
            "final_text": final_text
        }
        return json.dumps(output, indent=2)

    return final_text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenAI Golden Standard Transcription Tool")
    parser.add_argument("input", help="Path to audio file (WAV)")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        result = transcribe_openai(args.input, args.format)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
