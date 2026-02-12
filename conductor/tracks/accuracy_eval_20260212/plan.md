# Implementation Plan: Accuracy Comparison (Current vs v0.1)

Compare transcription accuracy and latency of `master` vs `v0.1` using headless `eval` mode.

## Phase 1: Baseline Execution (Master)
Goal: Capture performance metrics for the current state of the application.

- [ ] Task: Commit any uncommitted changes in the working directory to `master`.
- [ ] Task: Create output directory `eval_results/sample2_comparison/`.
- [ ] Task: Run `eval` on `master` for OpenAI and AssemblyAI providers.
    - [ ] Run: `uv run main.py eval --audio "C:\Users\alwat\OneDrive\Office\ Documents\Sound\ Recordings\voice2text_sample2.wav" --provider openai --timeout-seconds 120 > eval_results/sample2_comparison/master_openai.json`
    - [ ] Run: `uv run main.py eval --audio "C:\Users\alwat\OneDrive\Office\ Documents\Sound\ Recordings\voice2text_sample2.wav" --provider assemblyai --timeout-seconds 120 > eval_results/sample2_comparison/master_assemblyai.json`
- [ ] Task: Conductor - User Manual Verification 'Master Baselines Captured' (Protocol in workflow.md)

## Phase 2: Legacy Environment Setup (v0.1)
Goal: Create a functional evaluation environment for the legacy code.

- [ ] Task: Create temporary branch `temp/eval-v0.1` from tag `v0.1`.
- [ ] Task: Port minimal `eval` infrastructure to `temp/eval-v0.1`.
    - [ ] Copy `engine/eval_main.py` and `engine/audio/replay.py`.
    - [ ] Update legacy `main.py` with the CLI dispatcher for `eval`.
    - [ ] Ensure any missing dependencies (e.g., `numpy` usage in replayer) are handled.
- [ ] Task: Verify `eval` mode runs on the legacy branch with a short test.
- [ ] Task: Conductor - User Manual Verification 'Legacy Eval Ready' (Protocol in workflow.md)

## Phase 3: Legacy Execution & Comparison
Goal: Capture legacy metrics and generate the final report.

- [ ] Task: Run `eval` on `v0.1` for OpenAI and AssemblyAI providers.
    - [ ] Run: `uv run main.py eval --audio "C:\Users\alwat\OneDrive\Office\ Documents\Sound\ Recordings\voice2text_sample2.wav" --provider openai --timeout-seconds 120 > eval_results/sample2_comparison/v01_openai.json`
    - [ ] Run: `uv run main.py eval --audio "C:\Users\alwat\OneDrive\Office\ Documents\Sound\ Recordings\voice2text_sample2.wav" --provider assemblyai --timeout-seconds 120 > eval_results/sample2_comparison/v01_assemblyai.json`
- [ ] Task: Generate `eval_results/sample2_comparison/comparison_report.md`.
    - [ ] Compare transcription text (diff).
    - [ ] Tabulate latency metrics.
- [ ] Task: Switch back to `master` and delete the `temp/eval-v0.1` branch.
- [ ] Task: Conductor - User Manual Verification 'Comparison Complete' (Protocol in workflow.md)
