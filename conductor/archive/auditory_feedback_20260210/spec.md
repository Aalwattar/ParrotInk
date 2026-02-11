# Specification: Auditory Feedback for Recording State

## 1. Overview
This feature adds subtle auditory feedback to the recording lifecycle. To prevent "lost words" at the start of a session, the system will play a mild sound effect *only* after a successful connection to the transcription provider is established. A corresponding sound will play when the session stops. Users can enable/disable this feature via configuration and a tray menu toggle.

## 2. Functional Requirements

### 2.1 Sound Assets
- **Start Sound:** A soft, abstract "click" or "thud" sound.
- **Stop Sound:** A similar but distinct "closing" sound.
- **Storage:** Audio files will be bundled as built-in assets within the application (e.g., in `assets/sounds/`).

### 2.2 Execution Logic (Blocking Start)
- **Start Sequence:**
  1. User presses hotkey.
  2. Application initiates connection to provider (OpenAI/AssemblyAI).
  3. **Wait** for connection success confirmation.
  4. Play the "Start" sound.
  5. Immediately begin streaming audio capture to the provider.
- **Stop Sequence:**
  1. User triggers stop (key press, click away, etc.).
  2. Application stops audio capture and closes provider connection.
  3. Play the "Stop" sound.

### 2.3 Configuration
- **New configuration section in `config.toml` and `config.example.toml`:**
  ```toml
  [interaction.sounds]
  # Master toggle for audio feedback
  enabled = true
  # Volume level (0.0 to 1.0)
  volume = 0.5
  # Built-in paths (relative to app root or absolute)
  start_sound_path = "assets/sounds/start.wav"
  stop_sound_path = "assets/sounds/stop.wav"
  ```

### 2.4 User Interface
- **Tray Menu:** Add a "Settings" sub-menu.
- **Toggle:** Include an "Enable Audio Feedback" toggle (checked when enabled) in the sub-menu.
- **Persistence:** Changes to the toggle should update the internal state and be reflected in the configuration.

## 3. Non-Functional Requirements
- **Latency:** Sound playback must be low-latency and non-blocking to the main application logic.
- **Volume Control:** Sounds must be "very mild" and respect the configured volume level.
- **Reliability:** If audio assets are missing or playback fails, the application should continue to function normally (fail gracefully).

## 4. Acceptance Criteria
1. **Config Persistence:** The user can enable/disable sounds in `config.toml`, and the app respects this on startup.
2. **Connection Sync:** When starting dictation, the sound plays *after* the tray icon turns Red, and text starts appearing immediately after the sound (no lost words).
3. **Audibility:** Sounds are clear but subtle and not annoying over multiple uses.
4. **Toggle Control:** Disabling sounds in the tray menu stops all playback immediately.
5. **Resilience:** The app starts and functions even if the sound files are manually deleted from the disk.
