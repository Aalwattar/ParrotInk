# Implementation Plan: Accuracy Comparison (Current vs v0.1)

Compare transcription accuracy and latency of `master` vs `v0.1` using headless `eval` mode.

## Phase 1: Baseline Execution (Master)
Goal: Capture performance metrics for the current state of the application.

- [x] Task: Commit any uncommitted changes in the working directory to `master`. [d57b35e]
- [x] Task: Create output directory `eval_results/sample2_comparison/`. [d57b35e]
- [x] Task: Run `eval` on `master` for OpenAI and AssemblyAI providers. [7207599]
- [x] Task: Conductor - User Manual Verification 'Master Baselines Captured' (Protocol in workflow.md) [checkpoint: 7bb9bd8]

## Phase 2: Legacy Environment Setup (v0.1)
Goal: Create a functional evaluation environment for the legacy code.

- [x] Task: Create temporary branch `temp/eval-v0.1` from tag `v0.1`. [048c04e]
- [x] Task: Port minimal `eval` infrastructure to `temp/eval-v0.1`. [048c04e]
- [x] Task: Verify `eval` mode runs on the legacy branch with a short test. [048c04e]
- [x] Task: Conductor - User Manual Verification 'Legacy Eval Ready' (Protocol in workflow.md) [048c04e]

## Phase 3: Legacy Execution & Comparison
Goal: Capture legacy metrics and generate the final report.

- [x] Task: Run `eval` on `v0.1` for OpenAI and AssemblyAI providers. [048c04e]
- [x] Task: Generate `eval_results/sample2_comparison/comparison_report.md`. [048c04e]
- [x] Task: Switch back to `master` and delete the `temp/eval-v0.1` branch. [master]
- [x] Task: Conductor - User Manual Verification 'Comparison Complete' (Protocol in workflow.md)
