# Specification: Advanced Configuration & Test Mode

## 1. Overview
This track introduces a dedicated "Test Mode" and moves hardcoded API URLs into the configuration system. This allows developers to easily switch between local mock servers and production APIs without modifying source code.

## 2. Functional Requirements

### 2.1 Configuration Updates
- Add a new `[test]` section to `config.toml`.
- Implement an `enabled` boolean flag in the `[test]` section.
- Define production and mock URLs as configurable defaults in `engine/config.py`.

### 2.2 Provider Refactoring
- Refactor `OpenAIProvider` and `AssemblyAIProvider` to receive their connection URLs from the `Config` object instead of using hardcoded strings.
- Implement logic to switch the active URL based on the `test.enabled` flag:
    - If `test.enabled = true`: Use the predefined local mock URLs (e.g., `ws://localhost:8081`).
    - If `test.enabled = false`: Use the production API URLs.

### 2.3 Advanced Overrides
- Ensure that users can manually override the production URLs in `config.toml` if they need to point to a different endpoint (e.g., a proxy or a specific API version).

## 3. Technical Requirements
- Update the `Config` Pydantic model in `engine/config.py` to include the new `TestConfig` section and URL fields.
- Ensure the `AppCoordinator` correctly passes the selected URL to the `TranscriptionFactory`.

## 4. Acceptance Criteria
1. When `test.enabled = true` in `config.toml`, the application connects to the local mock server.
2. When `test.enabled = false` in `config.toml`, the application connects to the real OpenAI/AssemblyAI production endpoints.
3. Changing the URL in `config.toml` (if provided) overrides the internal defaults.
4. No hardcoded URL strings remain in the provider implementation files.

## 5. Out of Scope
- Implementing the mock servers themselves (assumed to already exist as `tests/mock_transcription_server.py`).
- Adding per-environment credentials (keys remain separate).
