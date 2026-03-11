# Implementation Plan: Support AssemblyAI Universal-3 Pro (u3-rt-pro) with Instructional Prompting

## Phase 1: Research & Investigation (HUD Delay)
- [x] Task: Investigate `u3-rt-pro` Partial Transcript Emission
    - [x] Create a debug script to monitor V3 websocket message timing.
    - [x] Analyze the frequency of `PartialTranscript` vs `FinalTranscript` (Turns).
    - [x] Confirm that `u3-rt-pro` has a longer stability window for partials.
- [x] Task: Evaluate Feasibility of "Shaded Partials" in HUD
    - [x] Research `skia-python` capabilities for multi-style text rendering.
    - [x] Determine if the `HUD` component can handle a "provisional" state for text.
- [x] Task: Comprehensive Architectural Review & Impact Analysis
    - [x] Map out all files to be modified (config, engine, UI).
    - [x] Document the proposed logic flow for instructional prompting and priority handling.
    - [x] Present a full architectural summary to the user for approval.
- [x] Task: Conductor - User Manual Verification 'Research & Investigation' (Protocol in workflow.md)

## Phase 2: Configuration & Core Support
- [x] Task: Update Configuration Schema
    - [x] Add `prompt` field to `AssemblyAIConfig` and `AssemblyAICoreConfig` in `engine/config.py`.
    - [x] Update `EffectiveAssemblyAIConfig` in `engine/app_types.py`.
    - [x] Add `partial_results` toggle to `TranscriptionConfig`.
- [x] Task: Update Configuration Resolver Logic
    - [x] Update `engine/config_resolver.py` to handle the `prompt` field.
    - [x] Implement priority logic: If `prompt` is present, ignore `keyterms_prompt` and log a warning.
- [x] Task: Update Example Configuration
    - [x] Add the new `prompt` field to `config.example.toml` with descriptive comments.
    - [x] Set default `speech_model` to `u3-rt-pro`.
- [x] Task: Conductor - User Manual Verification 'Configuration & Core Support' (Protocol in workflow.md)

## Phase 3: Engine Integration & Verification
- [x] Task: Update AssemblyAI Provider for V3
    - [x] Update `engine/transcription/assemblyai_provider.py` to handle `Turn` messages.
    - [x] Correctly route cumulative partials vs final transcripts.
- [x] Task: Implement Shaded Partials in HUD
    - [x] Update `engine/hud_styles.py` to support dual-text rendering (Committed vs Partial).
    - [x] Use Skia alpha/dimming for partial text.
    - [x] Update `engine/hud_renderer.py` and `engine/indicator_ui.py` to pass partial text through.
- [x] Task: Integration Test for `u3-rt-pro` with Prompt
    - [x] Update tests to verify the new config schema and V3 message handling.
- [x] Task: Conductor - User Manual Verification 'Engine Integration & Verification' (Protocol in workflow.md)

## Phase 4: Final Documentation & Cleanup
- [x] Task: Update README and Documentation
    - [x] Document the new model and prompting support in `README.md`.
- [x] Task: Conductor - User Manual Verification 'Final Documentation & Cleanup' (Protocol in workflow.md)
