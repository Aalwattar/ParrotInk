# Track Specification: Golden Standard Evaluation Tools

## Overview
Create independent, standalone Python tools to generate "Golden Standard" transcriptions for accuracy comparison. These tools use the highest-quality non-real-time (batch) APIs available from OpenAI and AssemblyAI, providing a performance ceiling benchmark for the project's real-time engine.

## 1. Functional Scope

### 1.1 Tool: `openai_golden.py`
- **Model:** `gpt-4o-transcribe` (High-quality Batch API).
- **Authentication:** Retrieve `openai_api_key` from Windows Credential Manager.
- **Features:** 
    - Support for high-quality file-based transcription using the latest GPT-4o based model.
    - Automatic audio chunking for files exceeding the 25MB OpenAI limit.
    - **JSON Output (Metadata Mode):**
        - Metadata: `provider`, `model` (gpt-4o-transcribe), `timestamp`, `audio_file`.
        - **API Config:** Request params (e.g., `language`, `prompt`).
        - Result: `final_text`.

### 1.2 Tool: `assemblyai_golden.py`
- **Model:** `Universal-3-Pro` (V3 Batch API).
- **Authentication:** Retrieve `assemblyai_api_key` from Windows Credential Manager.
- **Features:**
    - High-quality asynchronous transcription using the latest flagship model.
    - Polling logic to wait for completion.
    - **JSON Output (Metadata Mode):**
        - Metadata: `provider`, `model` (Universal-3-Pro), `timestamp`, `audio_file`.
        - **API Config:** Request params (e.g., `speech_model`, `punctuate`, `format_text`).
        - Result: `final_text`.

### 1.3 Common Infrastructure
- **Location:** `tests/golden_tools/`.
- **Independence:** Scripts must be runnable standalone, only depending on the project's `SecurityManager` for credentials.
- **Bulk Processing:** Support processing multiple files in one command.

## 2. Technical Goals
- **Benchmark Accuracy:** Provide the absolute highest accuracy possible for a given file.
- **Transparency:** Audit parameters sent to the API to ensure "Golden" runs are reproducible.

## 3. Acceptance Criteria
- [ ] `openai_golden.py` correctly uses `gpt-4o-transcribe`.
- [ ] `assemblyai_golden.py` correctly uses `Universal-3-Pro`.
- [ ] Both tools handle large files and produce structured JSON output.
- [ ] Tools fetch keys securely from the OS without hardcoded secrets.

## 4. Out of Scope
- Real-time transcription or low-latency streaming.
- UI components or system tray integration.
