# Specification: Secrets Management & Security (Final)

## 1. Overview
This track implements a modern, secure handling system for API keys. It moves away from storing secrets in configuration files entirely, utilizing the Windows Credential Manager (via `keyring`) as the primary storage. It introduces an interactive UI for managing these credentials while ensuring keys are never exposed in the interface.

## 2. Functional Requirements

### 2.1 Storage & Resolution Model
- **Strict Secure Storage:** API keys are stored only in the Windows Credential Manager.
- **Precedence Order:**
    1. **Windows Credential Manager (Keyring):** Primary source.
    2. **Environment Variables:** Secondary source for development/automated environments.
- **NO Config Fallback:** Literal keys in `config.toml` are strictly prohibited.
- **Service/Account Mapping:** Service `voice2text`, Accounts `openai_api_key`, `assemblyai_api_key`.

### 2.2 System Tray Credential Management
- **Menu Structure:** `Credentials` > `Set OpenAI Key...`, `Set AssemblyAI Key...`.
- **Absolute Privacy:** 
    - Keys are **never** displayed in the tray menu.
    - The input dialog for setting a key must use a password-style mask (e.g., `*`) for the entry field.
- **Immediate Update:** Saving a key updates the application's active session without requiring a restart.

### 2.3 Code Organization & Clean Architecture
- **Separation of Concerns:** All security logic is isolated in `engine/security.py`.
- **Module Responsibilities:**
    - `SecurityManager`: Centralized class for resolving and writing secrets.
    - `CredentialDialog`: Self-contained `tkinter` dialog for password-masked input.

### 2.4 Error Handling & Feedback
- **Credential Notifications:** The system must provide clear feedback if a key is missing or if a provider fails to authenticate.
- **Plumbing:** Implement a notification bridge (e.g., via `signals.py`) so the `SecurityManager` or Providers can trigger user-friendly error dialogs (e.g., "Invalid OpenAI Key", "AssemblyAI Key Expired").

## 3. Technical Requirements
- **Dependencies:** `keyring`.
- **Dialog:** `tkinter.simpledialog.askstring` with `show='*'` parameter.
- **Integration:** `AppCoordinator` uses the `SecurityManager` to resolve keys before initializing providers.

## 4. Acceptance Criteria
1. Tray menu shows "Set..." options but no key values.
2. Input dialog masks the characters as they are typed.
3. Keys are saved to `keyring` and the app immediately recognizes them.
4. No secrets exist in `config.toml`.
5. Code is cleanly separated into `engine/security.py`.
6. Missing or invalid keys trigger a user-friendly error message instead of a silent failure.

## 5. Out of Scope
- Retrieval of existing keys via UI.