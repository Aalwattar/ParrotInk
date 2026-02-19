# Track: Noise Reduction & Audio Profile Defaulting

**Goal:** Ensure the application defaults to an accuracy-optimized microphone profile rather than a raw ("none") profile, which has been identified as a cause of reduced transcription quality in noisy environments.

## Context
- **Issue:** Recent architectural changes set the default `mic_profile` to `none`. For OpenAI Realtime, this explicitly disables server-side noise reduction (`noise_reduction: null`), leading to poor accuracy in non-studio environments.
- **Requirement:** Change the default behavior to use a profile that enables noise reduction (e.g., `headset` or `laptop`) or ensure `none` is not the default for new users unless explicitly chosen.

## Plan
1.  **Analyze Defaults:** Check `engine/config.py` and `engine/config_resolver.py` for default values.
2.  **Update Config Schema:** Change the default `mic_profile` in `Config` model to a safe default (e.g., `headset` which maps to `near_field` or `laptop` which maps to `far_field`).
3.  **Verify Profile Mapping:** Ensure `engine/config_resolver.py` correctly translates this profile into the appropriate provider-specific settings (e.g., `noise_reduction: "server_vad"` or similar for OpenAI).
4.  **Test:** Verify that a fresh configuration generates the correct parameters.

## Outcome
- New users and reset configurations will default to a noise-reduced profile.
- Transcription accuracy should improve for users with background noise.
