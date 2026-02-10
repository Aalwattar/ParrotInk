# Implementation Plan: Secrets Management & Security

## Phase 1: Dependency & Architecture Setup [checkpoint: 4c7b3ae]
Set up the new module and move existing security concerns.

- [x] Task: Project structure and dependencies [4c7b3ae]
    - [x] Add `keyring` to `pyproject.toml`.
    - [x] Create `engine/security.py`.
    - [x] Update `.gitignore` to exclude `config.toml` and create `config.example.toml`.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Dependency & Architecture Setup' (Protocol in workflow.md)

## Phase 2: Security Module Implementation [checkpoint: 0f2dc3a]
Build the core logic for resolving and saving secrets.

- [x] Task: Implement `SecurityManager` in `engine/security.py` [0f2dc3a]
    - [x] Logic to lookup: Keyring -> Environment.
    - [x] Logic to save: Write to Keyring with service `voice2text`.
- [x] Task: Implement `CredentialDialog` [0f2dc3a]
    - [x] Simple `tkinter` dialog with password masking (`show='*'`).
- [x] Task: Write tests for `SecurityManager` [0f2dc3a]
    - [x] **Red:** Write tests in `tests/test_security.py` mocking `keyring` and `os.environ`.
    - [x] **Green:** Implement logic to pass the tests.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Security Module Implementation' (Protocol in workflow.md)

## Phase 3: Integration & UI
Connect the security module to the tray and coordinator.

- [~] Task: Update `Config` and `AppCoordinator`
    - [ ] Remove secret fields from `Config` (move to resolution logic).
    - [ ] Update `AppCoordinator` to use `SecurityManager` for provider initialization.
- [ ] Task: Update `TrayApp` UI
    - [ ] Add "Credentials" sub-menu with masked input triggers.
- [ ] Task: Implement Error Feedback Bridge
    - [ ] Add a mechanism (e.g., `show_error` signal) to display credential errors to the user.
- [ ] Task: Integration Test for Key Update & Error Handling
    - [ ] **Red:** Verify app triggers error if key is missing -> Update key via UI -> Verify connection works (mocked).
    - [ ] **Green:** Ensure UI triggers update and errors correctly.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Integration & UI' (Protocol in workflow.md)

## Phase 4: Final Verification & Cleanup
- [ ] Task: Verify no legacy keys remain
    - [ ] Audit `config.py` and `main.py` for any remaining hardcoded or config-based secret logic.
- [ ] Task: Final end-to-end smoke test
    - [ ] Set keys via UI and verify successful transcription and error reporting.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Final Verification & Cleanup' (Protocol in workflow.md)