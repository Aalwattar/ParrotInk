# Track Specification: Reliability & Configuration

## Overview
Enhance application reliability by improving session management, exposing hidden configuration knobs, and ensuring audio hardware compatibility. These changes address specific "invisible" issues that impact latency, user control, and hardware support.

## 1. Functional Scope

### 1.1 Immediate Session Rotation (I3)
- **Goal:** Reduce latency for the next dictation session.
- **Logic:** When dictation stops, if a rotation is pending (e.g., OpenAI 55m limit), the `ConnectionManager` should rotate the session immediately during idle time rather than waiting for the next "Start" command.

### 1.2 Configuration Knob Exposure (I4)
- **Goal:** Respect user settings for transcription and audio feedback.
- **OpenAI:** Map `config.providers.openai.advanced` settings (VAD threshold, silence duration, prefix padding) to the `session.update` call.
- **Audio Spec:** Use `config.audio.capture_sample_rate` (or provider-specific spec) instead of hard-coded constants where applicable.
- **Volume:** Implement the `volume` parameter in `engine/audio_feedback.py` using a system-compatible method or a lightweight library if necessary (fallback: scale PCM if we move to a different playback method, but for `winsound` we may be limited or need a different approach). *Self-correction: `winsound` doesn't support volume. I will investigate a lightweight alternative or document the limitation.*

### 1.3 Stereo Audio Fallback (I7)
- **Goal:** Ensure compatibility with high-end or non-standard audio interfaces.
- **Logic:** In `AudioStreamer`, if requesting 1 channel fails, automatically try requesting 2 channels. If 2 channels are granted, the existing downmix logic will handle the conversion to mono.

## 2. Technical Goals
- **Hardware Compatibility:** Zero-crash policy for devices that don't support mono capture.
- **Latency Optimization:** Ensure "Warm" connections are truly ready when the user presses the hotkey.
- **Config Purity:** Eliminate hard-coded "magic numbers" in provider implementations.

## 3. Acceptance Criteria
- [ ] OpenAI session rotates during IDLE state if pending.
- [ ] Changes to VAD settings in `config.toml` are correctly reflected in OpenAI logs.
- [ ] Application starts successfully on a stereo-only audio device.
- [ ] No regressions in standard dictation flow.
- [ ] Passes DOD Gate.
