# Specification: Configuration System Overhaul

Implement a robust configuration layer with a clear separation between user-facing TOML (`UserConfig`) and validated internal state (`EffectiveConfig`), while ensuring strict alignment with the latest OpenAI and AssemblyAI API specifications.

## 1. Overview
This track addresses configuration "messiness" and API drift by:
1.  **Staged Resolution:** Using a `ConfigResolver` to map high-level profiles to engineering values.
2.  **API Alignment:** Ensuring strict compliance with OpenAI Realtime Transcription and AssemblyAI Streaming V3.
3.  **Code Health:** Removing redundant fields and enforcing "Fail Fast" validation.

## 2. Functional Requirements

### 2.1. Staged Pipeline & Architecture
- **UserConfig:** Pydantic model exactly matching the TOML structure.
- **EffectiveConfig:** Derived, immutable settings passed via Constructor Injection.
- **Resolver Pipeline:** Parse -> Migrate -> Resolve (Profiles) -> Validate -> Compile.

### 2.2. User Profiles & Mappings
- **Latency Profiles:** `fast`, `balanced`, `accurate`.
    - `fast`: OpenAI (0.55/300ms), AssemblyAI (Aggressive)
    - `balanced`: OpenAI (0.60/500ms), AssemblyAI (Balanced)
    - `accurate`: OpenAI (0.65/800ms), AssemblyAI (Conservative)
- **Mic Profiles:** `headset`, `laptop`, `none`.
    - `headset`: OpenAI `near_field`
    - `laptop`: OpenAI `far_field`
    - `none`: OpenAI `null` (Off)
- **Single Source of Truth:** Global `language` and `audio.capture_sample_rate`.

### 2.3. OpenAI Realtime Alignment
- **Session Type:** Explicitly set `session.type = "transcription"`.
- **Format:** Force `audio/pcm` at `24000` Hz mono on-wire.
- **Model Separation:** Distinct `realtime_model` (transport URL) and `transcription_model` (ASR logic).

### 2.4. AssemblyAI V3 Alignment
- **V3 Endpoint:** Regional support (`us`, `eu`).
- **Cleanup:** Remove legacy `utterance_silence_threshold_ms`; omit `inactivity_timeout` if 0.
- **Formatting:** `format_text` boolean mapping to `format_turns`.

### 2.5. Diagnostics & Security
- **Explain Command:** `app config --explain` to show mapping logic.
- **Verbose Mode:** Preview raw provider payloads using existing `-v` flag.
- **Security:** Mandatory redaction of all secrets in any CLI output.

## 3. Technical Constraints
- **Pydantic:** Use Pydantic for both `UserConfig` (flexible) and `EffectiveConfig` (strict/immutable).
- **Constructor Injection:** Engine modules receive compiled settings; no direct TOML access.
- **Fail Fast:** Application must not start with invalid invariants.

## 4. Acceptance Criteria
- [ ] Application fails to start if config invariants are violated.
- [ ] No engine module reads the raw TOML or global config directly.
- [ ] API connections are verified clean (no "Unknown parameter" errors).
- [ ] `config.toml` is clean, user-friendly, and well-documented.
- [ ] `app config --explain` produces a readable, redacted report.

## 5. Out of Scope
-   Adding local DSP libraries.
-   Changing TOML to JSON/YAML.
