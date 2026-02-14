# Specification: Configuration Layer Refactor (EffectiveConfig & Validation)

Introduce a formal separation between the user-facing TOML configuration (`UserConfig`) and the internal, fully-resolved, and validated application state (`EffectiveConfig`).

## 1. Overview
This track implements a "Staged Pipeline" to resolve high-level user profiles into precise engineering values. It moves logic away from the providers and into a central `ConfigResolver`, ensuring the application engine consumes validated, domain-specific settings.

## 2. Functional Requirements

### 2.1. Staged Configuration Pipeline
Implement a `ConfigResolver` that executes the following stages:
1.  **Parse:** Read TOML into a `UserConfig` model (matches disk structure).
2.  **Resolve & Merge:** Handle `override` logic and merge user inputs with hardcoded defaults.
3.  **Derive & Compile:**
    -   Map `latency_profile` to specific VAD/Turn-detection timings.
    -   Map `mic_profile` to noise reduction enums.
    -   Enforce provider-specific invariants (e.g., OpenAI 24k rate).
4.  **Validate:** Perform cross-field checks.
    -   **Strictness:** Fail Fast. Raise exceptions and stop startup on invalid configs.

### 2.2. Domain-Specific "Compiled" Settings
The `EffectiveConfig` will be composed of specialized, immutable blocks passed via **Constructor Injection**:
-   `CompiledAudioSettings`: (Capture SR, resample targets, chunking).
-   `CompiledUiSettings`: (Refresh rate, max characters).
-   `CompiledProviders`: (Finalized OpenAI/AssemblyAI settings).

### 2.3. Config Explanation Command
Implement `app config --explain`.
-   **Primary Goal:** Print the resolved mapping logic (e.g., "Profile 'balanced' -> silence_duration_ms: 500").
-   **Integration:** Use the existing `-v`/`--verbose` flag to increase detail level (e.g., showing provider-specific payload structures if requested).
-   **Mandatory Security:** All output MUST redact API keys and sensitive credentials.

## 3. Technical Constraints
-   **Pydantic:** Use Pydantic for both `UserConfig` (flexible) and `EffectiveConfig` (strict/immutable).
-   **Code Organization:** Use specialized compilers (`compile_audio`, `compile_openai`) to keep the resolver maintainable.
-   **Provider Logic:** Providers should receive their `Compiled*Settings` and perform ZERO profile mapping logic themselves.

## 4. Acceptance Criteria
- [ ] Application fails to start if the configuration is invalid.
- [ ] `app config --explain` displays the resolution logic and redacted settings.
- [ ] No engine module reads the raw TOML or global config directly.
- [ ] Provider code is simplified by receiving pre-calculated values.

## 5. Out of Scope
-   A full-blown configuration GUI.
-   Auto-correcting user errors (must fail and inform).
