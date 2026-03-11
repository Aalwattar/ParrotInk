# Specification: Support AssemblyAI Universal-3 Pro (u3-rt-pro) with Instructional Prompting

## Overview
This track aims to integrate AssemblyAI's newest streaming model, **Universal-3 Pro (`u3-rt-pro`)**, into the ParrotInk engine. This includes adding support for instructional prompting, handling the mutual exclusivity between `prompt` and `keyterms_prompt`, and investigating the HUD's real-time responsiveness when using this new model.

## Functional Requirements
1.  **Configuration Support:**
    *   Update `AssemblyAIConfig` and `AssemblyAICoreConfig` in `engine/config.py` to include a `prompt` field (string).
    *   Set the default `speech_model` to `u3-rt-pro`.
    *   Update `config.example.toml` with the new default model and the recommended AssemblyAI instructional prompt.
2.  **Mutual Exclusivity Logic:**
    *   In `engine/config_resolver.py`, implement priority logic: if both `prompt` and `keyterms_prompt` are provided, the `prompt` takes precedence and `keyterms_prompt` is ignored (log a warning).
3.  **Instructional Prompting:**
    *   Ensure the `prompt` is correctly passed as a query parameter (`prompt`) to the AssemblyAI V3 WebSocket connection.
4.  **HUD Responsiveness Investigation:**
    *   Analyze why `u3-rt-pro` causes the HUD to only update after a pause.
    *   Evaluate if the engine can mimic AssemblyAI's own UI behavior where "unfinished" (partial) text is shown in a different shade or color in the HUD.
    *   **Constraint:** Investigate first; do not apply fixes to HUD behavior until the user confirms the findings.

## Non-Functional Requirements
1.  **Transparency:** Use clear comments in the configuration (TOML) and code explaining the mutual exclusivity of `prompt` and `keyterms_prompt`.
2.  **Backwards Compatibility:** Maintain support for older AssemblyAI models (e.g., `universal-streaming-english`) via the configuration.

## Acceptance Criteria
1.  Setting `speech_model = "u3-rt-pro"` in `config.toml` successfully connects to the new model.
2.  Providing a `prompt` in the configuration correctly influences the transcription output.
3.  If both `prompt` and `keyterms_prompt` are provided, the `prompt` is used and the word list is ignored.
4.  A detailed report on the HUD delay and "shaded partials" feasibility is provided to the user.

## Out of Scope
*   Adding the AssemblyAI prompt field to the Tray UI (requested as TOML-only).
