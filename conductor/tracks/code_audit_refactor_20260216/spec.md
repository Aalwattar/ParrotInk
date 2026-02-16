# Track Spec: Code Audit & Refactoring (Module-by-Module)

## Overview
Perform a systematic audit and refactoring of the codebase to improve maintainability, readability, and adherence to best practices. This includes eliminating hardcoded values, removing dead code, standardizing imports, and addressing major architectural/SOLID violations.

## Functional Requirements
- **Configuration Wiring**: Ensure all existing parameters in `config.toml` are correctly wired and respected throughout the engine.
- **De-hardcoding**:
    - Move local magic values to file-level constants.
    - Move shared values to a central constants location (if applicable).
    - **Propose** new user-configurable items only with justification and explicit user approval.
- **Dead Code Elimination**: Remove unused functions, classes, and orphaned imports.
- **Import Standardization**: Ensure all library and local imports are at the top of their respective files and follow a consistent order (Standard Lib -> Third Party -> Local).
- **Pragmatic SOLID Audit**: Identify and propose fixes for major architectural breaks (e.g., tight coupling between UI and Engine) on a case-by-case basis.

## Process Requirements
- **Module-by-Module Analysis**: The track will proceed module-by-module.
- **Approval Gate**: For each module, a report of findings must be presented and approved before any refactoring changes are implemented.

## Acceptance Criteria
- [ ] No magic strings or numbers remain in the active code paths.
- [ ] Every file follows a consistent structure (Imports -> Constants -> Logic).
- [ ] `config.toml` is the single source of truth for all tunable parameters.
- [ ] All 142+ tests pass after refactoring.

## Out of Scope
- Complete rewrite of the GUI or Audio pipelines (unless major breaks are found).
- Optimization for performance unless it's a byproduct of better architecture.
