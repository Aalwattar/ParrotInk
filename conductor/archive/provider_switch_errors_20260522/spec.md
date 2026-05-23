# Track Specification: Provider Switching & Error Handling Fixes

## Overview
This track addresses two critical bugs in the system, prioritizing a root-cause analysis approach:
1. **Provider Switch Regression:** Switching from AssemblyAI to OpenAI via the tray menu or hotkey fails silently (no log output). Since this is a fundamental feature that previously worked, the fix requires analyzing recent changes to understand why the signal is not being routed correctly before applying a minimal fix.
2. **Comprehensive Error Handling:** When a provider encounters an error (e.g., AssemblyAI `Unauthorized Connection: Insufficient funds`), it logs the error but the HUD and Tray Icon incorrectly remain in a "Ready" state. This track will implement a structured, best-practice error handling system that gracefully manages this error, as well as other potential errors identified from AssemblyAI and OpenAI documentation.

## Functional Requirements

### Bug 1: Provider Switching Regression
- **Root Cause Analysis:** Investigate the signal routing from the tray menu and hotkey to the provider manager. Determine why the switch event is not triggering any logs or actions.
- **Minimal Fix:** Apply a targeted fix to restore the signal routing without unnecessarily rewriting the existing switching mechanism.
- **Lazy Connection:** Once restored, ensure the new provider connection waits for the next user interaction (pressing the hotkey) to establish the connection ("Lazy Connect").

### Bug 2: Error Handling & Visibility
- **Error Discovery:** Systematically review the documentation for both AssemblyAI and OpenAI to compile a comprehensive list of potential critical errors (e.g., authentication, rate limits, credit exhaustion).
- **Structured Error Management:** Implement a robust, organized mechanism to catch and classify these specific errors gracefully.
- **HUD Error State:** When a critical error is encountered, the HUD status must immediately update to visually indicate an 'Error' state, explaining the failure (e.g., "Error: Insufficient funds").
- **Tray Icon Update:** The Tray Icon must transition to a warning/error state alongside the HUD update.

## Acceptance Criteria
- [ ] **Analysis Documented:** The root cause of the provider switching regression is clearly identified and documented in the implementation notes.
- [ ] **Test Provider Switch:** Selecting OpenAI from the tray menu while AssemblyAI is currently active, followed by pressing the hotkey, successfully routes the signal and generates a transcription.
- [ ] **Error Types Documented:** A structured list of handled errors for both AssemblyAI and OpenAI is documented in the codebase.
- [ ] **Test Error Feedback:** Simulating an AssemblyAI "insufficient funds" error correctly changes the HUD to display an Error state and updates the Tray Icon to a warning state.

## Out of Scope
- Windows Toast notifications for errors.
- Implementing automatic fallback to a secondary provider upon encountering an error.
