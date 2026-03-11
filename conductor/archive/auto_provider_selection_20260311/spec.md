# Specification: Auto-Select Provider and Refine Error Message

## 1. Overview
Currently, the application defaults to OpenAI as the transcription provider, which can cause confusion if a user has only configured an API key for AssemblyAI. This track implements a smart auto-selection mechanism that automatically switches the active provider if exactly one provider has a configured API key. It also refines the error message displayed when a provider is missing its API key to be more clear and actionable.

## 2. Functional Requirements

### 2.1 Smart Provider Auto-Selection
- **Condition for Auto-Switching:** If the currently selected provider is missing an API key, AND exactly one other provider has a valid API key configured, the application MUST automatically switch the active provider to the one with the valid key.
- **Timing:** This check and potential auto-switch must occur:
  - During application startup.
  - Dynamically whenever API keys are added, removed, or modified via the settings.
- **No Keys Fallback:** If NO API keys are configured for any provider, the application MUST retain the currently selected provider (e.g., keeping the default) rather than switching.
- **Multiple Keys:** If MULTIPLE providers have valid API keys, the application MUST NOT auto-switch the provider; it should respect the user's manual selection.

### 2.2 Refined Error Messaging
- **Updated Message Text:** When the active provider lacks a valid API key and a recording attempt is made (or a status is displayed), the error message MUST be explicitly updated to: `"Provider Missing API Key. Right-click Tray Icon > Settings to configure."`

## 3. Non-Functional Requirements
- **Performance:** Checking API key presence should be fast and not block the main or UI threads.
- **Config Fidelity:** Auto-switching a provider should update the underlying configuration file cleanly, respecting the `update_and_save` atomicity.

## 4. Acceptance Criteria
- [ ] If only an AssemblyAI key exists, starting the app with OpenAI as default automatically switches the provider to AssemblyAI.
- [ ] If no keys exist, the default provider remains unchanged.
- [ ] If both keys exist, the default provider remains unchanged.
- [ ] Deleting the active provider's key while another key exists immediately switches the active provider.
- [ ] Attempting to record without a valid key for the active provider displays the exact message: `"Provider Missing API Key. Right-click Tray Icon > Settings to configure."`

## 5. Out of Scope
- Adding support for entirely new transcription providers.
- Changing the foundational method by which API keys are stored (Windows Credential Manager).
