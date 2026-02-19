# Product Spec: Noise Reduction Defaults

**Objective:** Improve out-of-the-box transcription accuracy by defaulting to a microphone profile that includes noise reduction.

## Current State (Problem)
- **Default Profile:** `none`
- **OpenAI Behavior:** `noise_reduction: null` (Raw audio)
- **Impact:** Background noise (typing, fans) severely impacts accuracy.

## Proposed Change
- **Default Profile:** `headset` (Recommended for most desk setups) or `laptop` (Recommended for built-in mics).
- **Mapping:**
  - `headset` -> `near_field` (OpenAI: `server_vad`)
  - `laptop` -> `far_field` (OpenAI: `server_vad` + potentially different params if supported)
  - `none` -> `null` (Opt-in for advanced users)

## Acceptance Criteria
1.  **Default Config:** A fresh `Config()` instance must have `transcription.mic_profile` set to a non-null default (e.g., `headset`).
2.  **Existing Configs:** (Optional) If we can, migrate old configs, but standard practice is to let existing users keep their settings unless broken. We might just document this.
3.  **Config Resolver:** `resolve_effective_config` must correctly produce a `noise_reduction_type` string for OpenAI when the default profile is active.
