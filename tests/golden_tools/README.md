# Golden Standard Evaluation Tools

This directory contains standalone tools for generating high-quality "Golden Standard" transcriptions using batch (non-real-time) APIs. These benchmarks are used to evaluate the accuracy of the project's real-time transcription engine.

## Tools

### 1. OpenAI Golden Standard (`openai_golden.py`)
Uses the latest `gpt-4o-transcribe` model.
- **Features:** High-quality batch transcription, automatic audio chunking for files > 25MB.
- **Usage:**
  ```bash
  uv run python tests/golden_tools/openai_golden.py path/to/audio.wav --format json
  ```

### 2. AssemblyAI Golden Standard (`assemblyai_golden.py`)
Uses the flagship `Universal-3-Pro` model via the V3 Batch API.
- **Features:** State-of-the-art accuracy, asynchronous processing.
- **Usage:**
  ```bash
  uv run python tests/golden_tools/assemblyai_golden.py path/to/audio.wav --format json
  ```

## Authentication
Both tools retrieve API keys securely from the Windows Credential Manager using the project's `SecurityManager`. Ensure you have set your keys via the main application UI or `main.py set-key` command before running these tools.

## Output Formats
- `text` (default): Prints the final transcribed text to stdout.
- `json`: Prints a structured JSON object including the provider, model used, API configuration, and the final text.
