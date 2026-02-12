# Specification - verify_hud_isolation_20260212

## Overview
This track focuses on verifying that the recently implemented Skia-based HUD is architecturally isolated and optional. We need to ensure that the core transcription and injection logic remains untouched by the HUD implementation and that the application remains fully functional even if the HUD components (Skia/PyWin32) are missing or fail to initialize.

## Functional Requirements
- **Git Diff Validation**: Perform a detailed comparison against the `master` branch to ensure no "bleeding" of HUD logic into core engine components, or explain any necessary bridges.
- **Architectural Audit**: Confirm that all HUD-specific rendering and styling are contained within `engine/hud_renderer.py` and `engine/hud_styles.py`.
- **Optionality Enforcement**: Verify that `engine/indicator_ui.py` correctly handles the absence of `skia` by falling back to GDI or console logging without crashing the main application.

## Non-Functional Requirements
- **Test-Driven Verification**: The proof of "optionality" must be codified in a reusable automated smoke test.

## Acceptance Criteria
- [ ] A git diff report confirming core logic (`engine/audio/`, `engine/transcription/`) is unchanged or minimally impacted.
- [ ] Automated test `tests/test_hud_optionality.py` passes when HUD dependencies are mocked as missing.
- [ ] The application starts and performs a full transcription cycle (Start -> Capture -> Finalize) with the HUD explicitly disabled.

## Out of Scope
- Performance optimization of the HUD itself.
- Visual tweaks to the HUD design.
