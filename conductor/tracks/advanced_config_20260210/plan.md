# Implementation Plan: Advanced Configuration & Test Mode

## Phase 1: Configuration Schema & Defaults [checkpoint: fb27625]
Extend the configuration model to support test modes and URL overrides.

- [x] Task: Update `engine/config.py` with `TestConfig` and `AdvancedConfig` [39870a4]
    - [x] Add `TestConfig` class with `enabled`, `openai_mock_url`, and `assemblyai_mock_url`.
    - [x] Add `AdvancedConfig` class with production URLs for OpenAI and AssemblyAI.
    - [x] Update main `Config` class to include these sections as fields.
- [x] Task: Write tests for new configuration loading [39870a4]
    - [x] **Red:** Write tests in `tests/test_config.py` to verify defaults are populated.
    - [x] **Red:** Write tests to verify `config.toml` overrides for mock and production URLs work.
    - [x] **Green:** Ensure all config tests pass.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Configuration Schema & Defaults' (Protocol in workflow.md)

## Phase 2: Provider Refactoring [checkpoint: a6b0e26]
Remove hardcoded URLs from provider classes and inject them via the constructor.

- [x] Task: Update `BaseProvider` and implementations to accept `base_url` [a6b0e26]
    - [x] Update `BaseProvider.__init__` in `engine/transcription/base.py`.
    - [x] Refactor `OpenAIProvider` in `engine/transcription/openai_provider.py` to use `self.base_url`.
    - [x] Refactor `AssemblyAIProvider` in `engine/transcription/assemblyai_provider.py` to use `self.base_url`.
- [x] Task: Write unit tests for URL injection [a6b0e26]
    - [x] **Red:** Update provider tests to ensure they fail if URL is not provided or if they still use hardcoded strings.
    - [x] **Green:** Update tests to pass with injected URLs.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Provider Refactoring' (Protocol in workflow.md)

## Phase 3: Factory and Integration [checkpoint: 360cb22]
Update the factory logic to resolve URLs based on the test mode state.

- [x] Task: Update `TranscriptionFactory.create` to resolve URLs [360cb22]
    - [x] Implement logic in `factory.py` to choose between `test_url` and `production_url` based on `config.test.enabled`.
- [x] Task: Update `AppCoordinator` integration [360cb22]
    - [x] Ensure `AppCoordinator` in `main.py` passes the full `config` object to the factory.
- [x] Task: Write integration tests for URL resolution [360cb22]
    - [x] **Red:** Write a test that verifies the factory returns a provider pointing to `localhost` when `test.enabled` is True.
    - [x] **Green:** Ensure integration tests pass.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Factory and Integration' (Protocol in workflow.md)

## Phase 4: Final Smoke Test
Verify the system switches correctly between mock and live endpoints.

- [~] Task: Perform end-to-end smoke test
    - [ ] Run with `test.enabled = true` and verify connection to mock server.
    - [ ] Run with `test.enabled = false` and verify connection attempt to real OpenAI.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Final Smoke Test' (Protocol in workflow.md)
