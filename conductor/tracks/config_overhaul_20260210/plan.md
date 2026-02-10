# Implementation Plan: Granular Provider Configuration & AssemblyAI V3

## Phase 1: Configuration Schema Refactoring
Update the Pydantic models to support the new nested structure and remove legacy fields.

- [~] Task: Update `engine/config.py` with new models
    - [ ] Define `OpenAICoreConfig` and `OpenAIAdvancedConfig`.
    - [ ] Define `AssemblyAICoreConfig` and `AssemblyAIAdvancedConfig`.
    - [ ] Define `AudioConfig` (`capture_sample_rate`, `chunk_ms`).
    - [ ] Update main `Config` model to use these nested structures.
    - [ ] Remove legacy `AdvancedConfig` and its fields.
- [~] Task: Write tests for new configuration schema
    - [ ] **Red:** Write tests in `tests/test_config.py` that attempt to load the new nested structure.
    - [ ] **Green:** Ensure `Config.from_file` correctly parses the new schema and provides defaults.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Configuration Schema Refactoring' (Protocol in workflow.md)

## Phase 2: OpenAI Provider Enhancement
Update the OpenAI provider to consume the new granular settings.

- [ ] Task: Refactor `OpenAIProvider` connection logic
    - [ ] Use `realtime_ws_url_base` and `realtime_ws_model` to build the WebSocket URL.
    - [ ] Update session initialization to include `transcription_model`, `language`, and VAD settings from `advanced`.
- [ ] Task: Write tests for OpenAI provider updates
    - [ ] **Red:** Update `tests/test_transcription.py` to verify that the OpenAI provider uses the new config fields.
    - [ ] **Green:** Ensure tests pass (mocking the connection).
- [ ] Task: Conductor - User Manual Verification 'Phase 2: OpenAI Provider Enhancement' (Protocol in workflow.md)

## Phase 3: AssemblyAI V3 Migration
Migrate the AssemblyAI provider to the Streaming V3 API and support new parameters.

- [ ] Task: Refactor `AssemblyAIProvider` for V3
    - [ ] Update base URL to `wss://streaming.assemblyai.com/v3/ws`.
    - [ ] Implement query parameter builder for `sample_rate`, `word_boost`, `speech_model`, etc.
    - [ ] Update message handling if V3 protocol differs significantly (e.g., initialization message).
- [ ] Task: Write tests for AssemblyAI V3 migration
    - [ ] **Red:** Update `tests/test_transcription.py` to verify the new V3 URL construction and parameter mapping.
    - [ ] **Green:** Ensure tests pass (mocking the V3 connection).
- [ ] Task: Conductor - User Manual Verification 'Phase 3: AssemblyAI V3 Migration' (Protocol in workflow.md)

## Phase 4: Audio Integration & Documentation
Connect the global audio settings and finalize the project artifacts.

- [ ] Task: Update `AppCoordinator` and `AudioStreamer` integration
    - [ ] Ensure `AudioStreamer` uses `capture_sample_rate` from config.
    - [ ] Pass `chunk_ms` or calculated chunk size to the streamer/pipe.
- [ ] Task: Finalize documentation and examples
    - [ ] Update `config.example.toml` with the full new structure and comments.
    - [ ] Update `README.md` if any CLI examples or configuration tables changed.
- [ ] Task: Perform final smoke tests
    - [ ] Verify both providers connect successfully in Test Mode with the new config.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Audio Integration & Documentation' (Protocol in workflow.md)
