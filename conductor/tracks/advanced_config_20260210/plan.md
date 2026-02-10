# Implementation Plan: Advanced Configuration & Test Mode

## Phase 1: Configuration Schema & Defaults
Extend the configuration model to support test modes and URL overrides.

- [x] Task: Update `engine/config.py` with `TestConfig` and `AdvancedConfig` [39870a4]
    - [x] Add `TestConfig` class with `enabled`, `openai_mock_url`, and `assemblyai_mock_url`.
    - [x] Add `AdvancedConfig` class with production URLs for OpenAI and AssemblyAI.
    - [x] Update main `Config` class to include these sections as fields.
- [~] Task: Write tests for new configuration loading
    - [ ] **Red:** Write tests in `tests/test_config.py` to verify defaults are populated.
    - [ ] **Red:** Write tests to verify `config.toml` overrides for mock and production URLs work.
    - [ ] **Green:** Ensure all config tests pass.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Configuration Schema & Defaults' (Protocol in workflow.md)

## Phase 2: Provider Refactoring
Remove hardcoded URLs from provider classes and inject them via the constructor.

- [ ] Task: Update `BaseProvider` and implementations to accept `base_url`
    - [ ] Update `BaseProvider.__init__` in `engine/transcription/base.py`.
    - [ ] Refactor `OpenAIProvider` in `engine/transcription/openai_provider.py` to use `self.base_url`.
    - [ ] Refactor `AssemblyAIProvider` in `engine/transcription/assemblyai_provider.py` to use `self.base_url`.
- [ ] Task: Write unit tests for URL injection
    - [ ] **Red:** Update provider tests to ensure they fail if URL is not provided or if they still use hardcoded strings.
    - [ ] **Green:** Update tests to pass with injected URLs.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Provider Refactoring' (Protocol in workflow.md)

## Phase 3: Factory and Integration
Update the factory logic to resolve URLs based on the test mode state.

- [ ] Task: Update `TranscriptionFactory.create` to resolve URLs
    - [ ] Implement logic in `factory.py` to choose between `test_url` and `production_url` based on `config.test.enabled`.
- [ ] Task: Update `AppCoordinator` integration
    - [ ] Ensure `AppCoordinator` in `main.py` passes the full `config` object to the factory.
- [ ] Task: Write integration tests for URL resolution
    - [ ] **Red:** Write a test that verifies the factory returns a provider pointing to `localhost` when `test.enabled` is True.
    - [ ] **Green:** Ensure integration tests pass.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Factory and Integration' (Protocol in workflow.md)

## Phase 4: Final Smoke Test
Verify the system switches correctly between mock and live endpoints.

- [ ] Task: Perform end-to-end smoke test
    - [ ] Run with `test.enabled = true` and verify connection to mock server.
    - [ ] Run with `test.enabled = false` and verify connection attempt to real OpenAI.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Final Smoke Test' (Protocol in workflow.md)
