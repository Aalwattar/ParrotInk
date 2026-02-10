# Specification: Default Provider & UI Validation

## 1. Overview
This track renames the `active_provider` configuration setting to `default_provider` for better clarity and introduces dynamic UI validation. The application will now gray out providers in the system tray if their required credentials (API keys) are missing, unless the system is in "Test Mode".

## 2. Functional Requirements

### 2.1 Configuration Schema Update
- Rename the field `active_provider` to `default_provider` in `engine/config.py`.
- Ensure the configuration loader handles cases where `default_provider` might be missing by falling back to "openai".

### 2.2 Provider Availability Logic
- Implement a check to determine if a provider is "available":
    - **In Test Mode:** All providers are always available.
    - **In Production Mode:** A provider is only available if its corresponding API key (e.g., `openai_api_key`) is present and not empty.

### 2.3 UI Integration (System Tray)
- Update `TrayApp` in `engine/ui.py` to receive the "availability" status of each provider.
- **Gray Out Logic:** If a provider is not available, its menu item in the system tray must be disabled (unclickable).
- **Startup Fallback:** If the `default_provider` defined in the config is not available, the app should automatically switch to the first available provider or show an error state if none are available.

## 3. Technical Requirements
- Update `Config` Pydantic model in `engine/config.py`.
- Add an `is_available(provider_name, config)` helper method or similar logic to the `AppCoordinator` or `TranscriptionFactory`.
- Update `engine/ui.py` to support disabling specific menu items.

## 4. Acceptance Criteria
1. The application starts correctly using `default_provider` from `config.toml`.
2. If `openai_api_key` is empty and `test.enabled` is false, the "OpenAI" option in the tray menu is grayed out.
3. If `assemblyai_api_key` is empty and `test.enabled` is false, the "AssemblyAI" option in the tray menu is grayed out.
4. If both are missing, the UI reflects an error or restricted state.
5. In Test Mode, all options remain enabled regardless of key presence.

## 5. Out of Scope
- Automatically opening the config file when a provider is disabled.
- Validating the *correctness* of the API keys (only checking for presence/emptiness).
