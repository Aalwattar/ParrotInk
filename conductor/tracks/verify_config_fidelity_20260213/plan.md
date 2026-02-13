# Implementation Plan: Verify Config Fidelity

- [x] **Step 1: AssemblyAI Fixes** [2eace4b]
    - Audit `assemblyai_provider.py`.
    - Replace hardcoded values (350, 1200, 0.4) with `config` references.
    - Ensure `config.py` has the corresponding fields in `AssemblyAIAdvancedConfig` or `Core`.

- [x] **Step 2: OpenAI Audit & Fixes** [2eace4b]
    - Audit `openai_provider.py`.
    - Check `session.update` payload construction.
    - Ensure `noise_reduction`, `prefix_padding_ms`, `silence_duration_ms` are correctly mapped.

- [x] **Step 3: Config Schema Updates** [2eace4b]
    - If any parameter is missing from `config.py`, add it to the Pydantic models.

- [x] **Step 4: Verification** [2eace4b]
    - Run `pytest` to ensure no regressions.
    - (Manual) Verify `_build_url` logic via inspection.
