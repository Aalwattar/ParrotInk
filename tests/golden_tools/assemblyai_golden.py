import argparse
import json
import os
import sys
from datetime import datetime

import assemblyai as aai

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from tests.golden_tools.auth_utils import get_assemblyai_key


def transcribe_assemblyai(audio_path: str, format: str = "text"):
    aai.settings.api_key = get_assemblyai_key()

    config = aai.TranscriptionConfig(
        speech_models=["universal-3-pro"],
        punctuate=True,
        format_text=True
    )

    transcriber = aai.Transcriber()

    print(f"Uploading and transcribing {audio_path} using Universal-3-Pro...", file=sys.stderr)
    transcript = transcriber.transcribe(audio_path, config=config)

    if transcript.status == aai.TranscriptStatus.error:
        raise Exception(f"Transcription failed: {transcript.error}")

    final_text = transcript.text
    print("Transcription complete.", file=sys.stderr)

    if format == "json":
        output = {
            "status": "ok",
            "provider": "assemblyai",
            "model": "Universal-3-Pro",
            "timestamp": datetime.now().isoformat(),
            "audio_file": audio_path,
            "api_config": {
                "speech_model": "universal-3-pro",
                "punctuate": True,
                "format_text": True
            },
            "final_text": final_text
        }
        return json.dumps(output, indent=2)

    return final_text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AssemblyAI Golden Standard Transcription Tool")
    parser.add_argument("input", help="Path to audio file")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        result = transcribe_assemblyai(args.input, args.format)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
