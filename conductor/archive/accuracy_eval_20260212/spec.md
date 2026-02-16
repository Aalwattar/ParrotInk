# Track Specification: Accuracy Comparison (Current vs v0.1)

## Overview
Compare the transcription accuracy and latency of the current `master` branch against the legacy `v0.1` tag using the headless `eval` mode. This will help determine if recent architectural changes have impacted the quality of transcription.

## 1. Functional Requirements

### 1.1 Test Assets
- **Audio File:** `C:\Users\alwat\OneDrive\Office\ Documents\Sound\ Recordings\parrotink_sample2.wav`
- **Providers:** `openai`, `assemblyai`

### 1.2 Target Versions
- **Current Version:** The code at the current `master` HEAD.
- **Legacy Version (v0.1):** 
    - Create a temporary branch `temp/eval-v0.1` from tag `v0.1`.
    - Port the `eval` functionality (`engine/eval_main.py`, `engine/audio/replay.py`, and CLI dispatcher) to this branch.
    - **CRITICAL:** Ensure the core transcription and audio capture logic of `v0.1` is not modified.

### 1.3 Execution & Storage
- **Output Directory:** `eval_results/sample2_comparison/`
- **Runs:** Perform 4 evaluation runs (Master-OpenAI, Master-AssemblyAI, v0.1-OpenAI, v0.1-AssemblyAI).
- **Reporting:** Generate a `comparison_report.md` summarizing the differences in:
    - Final transcription text.
    - Time to First Partial.
    - Time to First Final.

## 2. Technical Goals
- **Fair Comparison:** Use identical audio and chunking settings for both versions.
- **Isolation:** The temporary branch must be deleted after the results are captured.

## 3. Acceptance Criteria
- [ ] Raw JSON results for all 4 runs are saved in the output directory.
- [ ] `comparison_report.md` is generated with an accuracy and speed analysis.
- [ ] No permanent changes are made to the `v0.1` history or current `master` engine.

## 4. Out of Scope
- Fixing accuracy issues discovered during this track (discovery only).
- Permanent maintenance of the ported `eval` code on the legacy branch.
