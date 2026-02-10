# Implementation Plan: Granular Provider Configuration & AssemblyAI V3

## Phase 1: Configuration Schema Refactoring [checkpoint: d14d0ce]
Update the Pydantic models to support the new nested structure and remove legacy fields.

- [x] Task: Update `engine/config.py` with new models [d14d0ce]
    - [x] Define `OpenAICoreConfig` and `OpenAIAdvancedConfig`.
    - [x] Define `AssemblyAICoreConfig` and `AssemblyAIAdvancedConfig`.
    - [x] Define `AudioConfig` (`capture_sample_rate`, `chunk_ms`).
    - [x] Update main `Config` model to use these nested structures.
    - [x] Remove legacy `AdvancedConfig` and its fields.
- [x] Task: Write tests for new configuration schema [d14d0ce]
    - [x] **Red:** Write tests in `tests/test_config.py` that attempt to load the new nested structure.
    - [x] **Green:** Ensure `Config.from_file` correctly parses the new schema and provides defaults.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Configuration Schema Refactoring' (Protocol in workflow.md) [d14d0ce]

## Phase 2: OpenAI Provider Enhancement [checkpoint: 337449a]
Update the OpenAI provider to consume the new granular settings.

- [x] Task: Refactor `OpenAIProvider` connection logic [337449a]
    - [x] Use `realtime_ws_url_base` and `realtime_ws_model` to build the WebSocket URL.
    - [x] Update session initialization to include `transcription_model`, `language`, and VAD settings from `advanced`.
- [x] Task: Write tests for OpenAI provider updates [337449a]
    - [x] **Red:** Update `tests/test_transcription.py` to verify that the OpenAI provider uses the new config fields.
    - [x] **Green:** Ensure tests pass (mocking the connection).
- [x] Task: Conductor - User Manual Verification 'Phase 2: OpenAI Provider Enhancement' (Protocol in workflow.md) [337449a]

## Phase 3: AssemblyAI V3 Migration [checkpoint: 337449a]
Migrate the AssemblyAI provider to the Streaming V3 API and support new parameters.

- [x] Task: Refactor `AssemblyAIProvider` for V3 [337449a]
    - [x] Update base URL to `wss://streaming.assemblyai.com/v3/ws`.
    - [x] Implement query parameter builder for `sample_rate`, `word_boost`, `speech_model`, etc.
    - [x] Update message handling if V3 protocol differs significantly (e.g., initialization message).
- [x] Task: Write tests for AssemblyAI V3 migration [337449a]
    - [x] **Red:** Update `tests/test_transcription.py` to verify the new V3 URL construction and parameter mapping.
    - [x] **Green:** Ensure tests pass (mocking the V3 connection).
- [x] Task: Conductor - User Manual Verification 'Phase 3: AssemblyAI V3 Migration' (Protocol in workflow.md) [337449a]

## Phase 4: Audio Integration & Documentation [checkpoint: 337449a]
Connect the global audio settings and finalize the project artifacts.

- [x] Task: Update `AppCoordinator` and `AudioStreamer` integration [337449a]
    - [x] Ensure `AudioStreamer` uses `capture_sample_rate` from config.
    - [x] Pass `chunk_ms` or calculated chunk size to the streamer/pipe.
- [x] Task: Finalize documentation and examples [337449a]
    - [x] Update `config.example.toml` with the full new structure and comments.
    - [x] Update `README.md` if any CLI examples or configuration tables changed.
- [x] Task: Perform final smoke tests [337449a]
    - [x] Verify both providers connect successfully in Test Mode with the new config.
- [x] Task: Conductor - User Manual Verification 'Phase 4: Audio Integration & Documentation' (Protocol in workflow.md) [337449a]