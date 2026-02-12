# Implementation Plan: Golden Standard Evaluation Tools

Create standalone benchmark tools using high-quality batch APIs.

## Phase 1: Infrastructure & Shared Utilities
Goal: Setup the tool directory and provide a secure way to access existing API keys.

- [x] Task: Create directory `tests/golden_tools/`.
- [x] Task: Create `tests/golden_tools/auth_utils.py` to wrap `SecurityManager` for standalone use.
- [x] Task: Verify that `auth_utils.py` can correctly fetch keys from Windows Credential Manager.
- [x] Task: Conductor - User Manual Verification 'Auth Infrastructure Verified' (Protocol in workflow.md)

## Phase 2: OpenAI Golden Tool
Goal: Implement the high-quality OpenAI benchmark tool.

- [x] Task: Implement `tests/golden_tools/openai_golden.py` using `openai.Audio.transcriptions` with `gpt-4o-transcribe`.
- [x] Task: Implement automatic audio chunking (using `pydub` or similar) if file > 25MB.
- [x] Task: Implement JSON output mode with `final_text` and API metadata.
- [x] Task: Verify `openai_golden.py` with a short sample file.
- [x] Task: Conductor - User Manual Verification 'OpenAI Golden Verified' (Protocol in workflow.md)

## Phase 3: AssemblyAI Golden Tool
Goal: Implement the high-quality AssemblyAI benchmark tool.

- [x] Task: Implement `tests/golden_tools/assemblyai_golden.py` using `assemblyai.Transcriber` with `Universal-3-Pro`.
- [x] Task: Implement asynchronous polling logic for batch results.
- [x] Task: Implement JSON output mode with metadata.
- [x] Task: Verify `assemblyai_golden.py` with a short sample file.
- [x] Task: Conductor - User Manual Verification 'AssemblyAI Golden Verified' (Protocol in workflow.md)

## Phase 4: Finalization & Documentation
Goal: Ensure the tools are easy to use and well-documented.

- [ ] Task: Add a `README.md` in `tests/golden_tools/` explaining usage.
- [ ] Task: Run DOD Gate (Ruff, Mypy, Pytest) on the new tools.
- [ ] Task: Conductor - User Manual Verification 'Tools Finalized' (Protocol in workflow.md)
