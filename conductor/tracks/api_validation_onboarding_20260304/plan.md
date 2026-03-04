# Implementation Plan: API Key Validation & Onboarding

## Strategy
1.  Add a `validate_key(provider, key)` helper to `engine/config.py`.
2.  Update `main.py` to use this helper in `get_provider_availability`.
3.  Update `main.py` to show a HUD onboarding message if `start_listening` is called with an invalid key.
4.  Update `engine/ui.py` to disable the "Start" menu item if the key is invalid. (Actually, there's no start menu item, so I'll skip this or add one if requested, but for now I'll focus on the hotkey).
5.  Wait, there is a `Start` menu item in some versions? No, I checked `ui.py`.

## Proposed Changes

### 1. `engine/config.py`
-   Add `is_api_key_valid(provider: str, key: Optional[str]) -> bool`
    -   For `openai`: must start with `sk-` (or `sk-proj-` for project keys).
    -   For `assemblyai`: must be a hex string of 32 characters.
    -   Reject placeholders like "4444", "YOUR_API_KEY", etc.

### 2. `main.py`
-   Refine `get_provider_availability` to use `is_api_key_valid`.
-   Update `start_listening`:
    -   If the key is missing/invalid, call `self.ui_bridge.show_onboarding_message()`.

### 3. `engine/ui_bridge.py` & `engine/hud_renderer.py`
-   Add `show_onboarding_message()` to `UIBridge`.
-   Implement it in `HUDRenderer` to show "API Key Required\nGo to Settings to add it" in a distinct style.

## Verification Plan
1.  **Manual Test**: Clear API keys from keyring/env. Press hotkey.
    -   Expect: HUD shows "API Key Required".
2.  **Manual Test**: Set API key to "4444". Press hotkey.
    -   Expect: HUD shows "API Key Required".
3.  **Automated Test**: Add a test case in `tests/test_config.py` for key validation logic.
