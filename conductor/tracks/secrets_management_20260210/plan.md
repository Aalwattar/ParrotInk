# Implementation Plan: Secrets Management & Security

## Phase 1: Environment & Dependency Setup
Set up the necessary security boundaries and install dependencies.

- [ ] Task: Update project dependencies and repository structure
    - [ ] Add `keyring` to `pyproject.toml`.
    - [ ] Create `config.example.toml` with placeholder values and usage instructions.
    - [ ] Update `.gitignore` to explicitly exclude `config.toml`.
- [ ] Task: Verify dependency installation
    - [ ] **Red:** Write a small script to attempt importing `keyring` and verify it fails if not installed.
    - [ ] **Green:** Run `uv sync` and verify the script now succeeds.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Environment & Dependency Setup' (Protocol in workflow.md)

## Phase 2: Secret Resolution Logic
Implement the logic to resolve secrets from Keyring, Environment, or Literal values.

- [ ] Task: Implement `SecretResolver` utility
    - [ ] Create a utility that takes a reference string and performs the tiered lookup (Keyring -> Env -> Literal).
    - [ ] Use `voice2text` as the default service name for `keyring`.
- [ ] Task: Write unit tests for secret resolution
    - [ ] **Red:** Write tests in `tests/test_security.py` that mock `keyring` and `os.environ` to verify precedence.
    - [ ] **Green:** Implement the resolver to pass the tests.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Secret Resolution Logic' (Protocol in workflow.md)

## Phase 3: Configuration Integration
Integrate the resolver into the configuration loading process.

- [ ] Task: Update `Config` model to resolve secrets
    - [ ] Update `engine/config.py` to apply the resolver to credential fields after loading the TOML.
- [ ] Task: Write tests for secure config loading
    - [ ] **Red:** Write tests ensuring that if a field matches a keyring entry, the `Config` object contains the secret, not the reference string.
    - [ ] **Green:** Ensure all configuration security tests pass.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Configuration Integration' (Protocol in workflow.md)

## Phase 4: Final Security Audit
Ensure no secrets are leaked and the system is robust.

- [ ] Task: Verify `.gitignore` and `config.example.toml`
    - [ ] Run `git check-ignore config.toml` to confirm protection.
    - [ ] Ensure `config.example.toml` is correctly committed and tracked.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Final Security Audit' (Protocol in workflow.md)
