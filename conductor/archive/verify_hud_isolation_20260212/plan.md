# Implementation Plan - verify_hud_isolation_20260212

## Phase 1: Context & Diff Analysis
- [ ] Task: Baseline Comparison
    - [ ] Run `git fetch origin master` to ensure local master is up to date.
    - [ ] Execute `git diff origin/master --stat` to identify all modified files.
    - [ ] Perform a deep-dive `git diff origin/master engine/` to check for any coupling in the core engine.
- [ ] Task: Logical Isolation Audit
    - [ ] Verify `main.py` only interacts with the HUD via the `UIBridge`.
    - [ ] Verify `engine/indicator_ui.py` uses robust `try...except` or feature-flag guards for HUD imports.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Context & Diff Analysis' (Protocol in workflow.md)

## Phase 2: Automated Optionality Testing
- [ ] Task: Write Optionality Smoke Test
    - [ ] Create `tests/test_hud_optionality.py`.
    - [ ] Implement a test case that mocks `import skia` to fail.
    - [ ] Assert that `IndicatorWindow` falls back to `GdiFallbackWindow` or a safe null-op without raising exceptions.
- [ ] Task: Execute Test Suite
    - [ ] Run `pytest tests/test_hud_optionality.py` to verify the fallback logic.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Automated Optionality Testing' (Protocol in workflow.md)

## Phase 3: Runtime Verification
- [ ] Task: Manual "No-HUD" Run
    - [ ] Temporarily modify `engine/hud_renderer.py` to force `HUD_AVAILABLE = False`.
    - [ ] Run `uv run python main.py` and perform a voice-to-text session.
    - [ ] Confirm transcription is still injected into the active window correctly.
- [ ] Task: Definition of Done Gate
    - [ ] Run `ruff check .`.
    - [ ] Run `ruff format --check .`.
    - [ ] Run `mypy .`.
    - [ ] Run full `pytest` suite.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Runtime Verification' (Protocol in workflow.md)
