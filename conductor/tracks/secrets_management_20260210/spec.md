# Specification: Secrets Management & Security

## 1. Overview
This track implements secure handling of API keys and sensitive credentials. The application will transition from storing literal keys in `config.toml` to a secure lookup model using the Windows Credential Manager (via `keyring`) and environment variables.

## 2. Functional Requirements

### 2.1 Secret Lookup Logic
- Implement a tiered lookup system for all credential fields (e.g., `openai_api_key`, `assemblyai_api_key`).
- **Precedence Order:**
    1. **Windows Credential Manager (Keyring):** Look up using the value from `config.toml` as the "Account Name".
    2. **Environment Variables:** Look up using the value from `config.toml` as the variable name.
    3. **Literal Fallback:** Use the value in `config.toml` as the literal secret (primarily for development or quick start).

### 2.2 Security Best Practices
- **`config.example.toml`:** Create a template file containing only placeholder values and comments.
- **Git Protection:** Update `.gitignore` to ensure `config.toml` and any files containing real secrets are never committed to the repository.
- **Dependency Management:** Add `keyring` to the project dependencies.

### 2.3 Configuration Integration
- The `Config` loader in `engine/config.py` must be updated to resolve these secrets at runtime before they are passed to the providers.

## 3. Technical Requirements
- Add `keyring` to `pyproject.toml`.
- Create a `SecretResolver` utility or integrate logic into `Config` to handle the `keyring` and `os.environ` lookups.
- Service name for `keyring` should be standardized (e.g., `voice2text`).

## 4. Acceptance Criteria
1. A `config.example.toml` exists with clear instructions.
2. If `openai_api_key = "MY_OPENAI_KEY"` is in `config.toml`, and `MY_OPENAI_KEY` exists in Windows Credentials, the app uses that secret.
3. If not in Windows Credentials but `MY_OPENAI_KEY` is an environment variable, the app uses that value.
4. If neither exist, the app uses `"MY_OPENAI_KEY"` as the literal API key.
5. The `.gitignore` successfully prevents `config.toml` from being tracked.

## 5. Out of Scope
- Implementing a GUI for managing/saving keys into the Windows Credential Manager (users must add them manually or via CLI for now).
- Encryption of the local `config.toml` file itself.
