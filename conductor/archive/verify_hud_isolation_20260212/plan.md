# Implementation Plan - verify_hud_isolation_20260212

## Phase 1: Context & Diff Analysis
- [x] Task: Baseline Comparison
    - [x] Run `git fetch origin master` to ensure local master is up to date.
    - [x] Execute `git diff origin/master --stat` to identify all modified files.
    - [x] Perform a deep-dive `git diff origin/master engine/` to check for any coupling in the core engine.
- [x] Task: Logical Isolation Audit
    - [x] Verify `main.py` only interacts with the HUD via the `UIBridge`.
    - [x] Verify `engine/indicator_ui.py` uses robust `try...except` or feature-flag guards for HUD imports.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Context & Diff Analysis' (Protocol in workflow.md)

## Phase 2: Automated Optionality Testing
- [x] Task: Write Optionality Smoke Test
    - [x] Create `tests/test_hud_optionality.py`.
    - [x] Implement a test case that mocks `import skia` to fail.
    - [x] Assert that `IndicatorWindow` falls back to `GdiFallbackWindow` or a safe null-op without raising exceptions.
- [x] Task: Execute Test Suite
    - [x] Run `pytest tests/test_hud_optionality.py` to verify the fallback logic.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Automated Optionality Testing' (Protocol in workflow.md)

## Phase 3: Runtime Verification
- [x] Task: Manual "No-HUD" Run
    - [x] Temporarily modify `engine/hud_renderer.py` to force `HUD_AVAILABLE = False`.
    - [x] Run `uv run python main.py` and perform a voice-to-text session.
    - [x] Confirm transcription is still injected into the active window correctly.
- [x] Task: Definition of Done Gate
    - [x] Run `ruff check .`.
    - [x] Run `ruff format --check .`.
    - [x] Run `mypy .`.
    - [x] Run full `pytest` suite.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Runtime Verification' (Protocol in workflow.md)
