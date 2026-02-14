# Specification: Unified Configuration & Interaction Overhaul

Modernize the configuration system and user interaction flow by implementing high-level profiles, strict API compliance, and an interactive hotkey recording mechanism.

## 1. Overview
This track eliminates the "messy" state of the current configuration and provides a professional UI for hotkey management. It prioritizes using existing code (the `Config` class and `AppCoordinator`) over adding redundant layers.

## 2. Functional Requirements

### 2.1. Refined Configuration Schema
- **User Profiles:** 
  - `latency_profile`: `fast`, `balanced`, `accurate` (Internal mapping to VAD/Turn-detection).
  - `mic_profile`: `headset`, `laptop`, `none` (Maps to OpenAI Noise Reduction).
- **Consolidation:**
  - Single source of truth for `language` and `audio.capture_sample_rate`.
  - Documentation: Clarify `sounds.volume` range (0.0 to 1.0) and `anchor_scope="control"` status as experimental/fallback.

### 2.2. Provider API Alignment (Latest Specs)
- **OpenAI Realtime:**
  - Explicit `session.type = "transcription"`.
  - Force `audio/pcm` @ `24000` Hz.
  - Separate `realtime_model` (transport) and `transcription_model` (ASR logic).
- **AssemblyAI Streaming V3:**
  - Regional support (`us`, `eu`).
  - Map `format_text` to `format_turns`.
  - Remove legacy `utterance_silence_threshold_ms`.

### 2.3. Smart "In-Flight" Updates
- **Update Mechanism:** Enhance the `Config` class with a method to update settings in memory and persist to `config.toml` immediately.
- **Engine Notification:** When critical settings (like the hotkey) are updated while the app is running, the `AppCoordinator` or relevant monitor must be notified to re-initialize the listener without a restart.

### 2.4. Interactive Hotkey UI
- **Tray Menu:** Add a "Change Hotkey" option.
- **Recording Dialog:** A Win32 modal prompt that captures the next key combination.
- **Validation:** 
  - Reject system-reserved keys (Win+L, Alt+F4, etc.).
  - If invalid, keep the dialog open and provide feedback.
- **Auto-Sync:** On valid capture, use the "In-Flight Update" mechanism to persist and apply.

### 2.5. Diagnostics & Safety
- **Explain Command:** `app config --explain` to show mapping logic and redacted settings.
- **Fail Fast:** Show a clear Win32 Message Box and exit if the TOML configuration is fundamentally broken at startup.

## 3. Technical Constraints
- **Pydantic Validation:** Enforce strict ranges and enums in the schema.
- **No Redundant Layers:** Use existing classes; avoid creating separate "SyncServices" or "Monolith Resolvers."
- **Secrets Redaction:** Mask all keys in CLI output.

## 4. Acceptance Criteria
- [ ] Application starts correctly with the new profile-based config.
- [ ] User can record a new hotkey via the tray; it works immediately and saves to disk.
- [ ] OpenAI and AssemblyAI connections are clean and aligned with the latest docs.
- [ ] Invalid hotkeys are rejected with a helpful UI message.
- [ ] `app config --explain` displays correctly.
