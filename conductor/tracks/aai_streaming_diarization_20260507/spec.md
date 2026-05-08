# Design Spec: AssemblyAI Streaming Diarization (Major Upgrade)

**Date:** 2026-05-07
**Status:** Draft
**Feature Branch:** `feature/aai-streaming-diarization`

## 1. Goal
Implement support for AssemblyAI's upgraded streaming diarization (speaker labeling) using the new word-level speaker labels. This will allow ParrotInk to identify multiple speakers in real-time meetings with high precision.

## 2. Requirements
- **Configurable:** Must be disabled by default. Controlled via `providers.assemblyai.advanced.enable_diarization`.
- **Modular:** Core transcription logic should remain stable. Diarization logic must be isolated.
- **Visual Style:** Use the "Compact" format `[S1] Text...` in the HUD.
- **Reliability:** If diarization fails or is disabled, the system must fallback gracefully to standard single-speaker transcription.

## 3. Architecture
- **`engine/config.py`**: Add `enable_diarization: bool = False` to `AssemblyAIAdvancedConfig`.
- **`engine/config_resolver.py`**: Append `&speaker_labels=true` to the AssemblyAI WS URL only when enabled.
- **`engine/transcription/speaker_manager.py` (New)**:
    - A standalone class to track current speaker state.
    - Processes `event.get("words", [])` from AssemblyAI.
    - Detects speaker changes and prepends `[SX]` to the transcript segments.
- **`engine/transcription/assemblyai_provider.py`**:
    - Integrate `SpeakerManager` optionally.
    - Update `_handle_event` to use the manager for formatting if active.

## 4. UI/HUD Implementation
- We will use the **Compact [S1]** style.
- The `SpeakerManager` will handle the string formatting so the HUD receives a standard string: `"[S1] Hello world"`.
- This avoids modifying the complex HUD rendering logic in `engine/hud_renderer.py`.

## 5. Testing Strategy
- **Unit Tests**: Test `SpeakerManager` with mock AssemblyAI JSON payloads containing word-level labels.
- **Integration Tests**: A new test `tests/test_aai_diarization.py` to verify the config toggle correctly modifies the WS URL.
- **Manual Verification**: Run with a recorded multi-speaker audio file through the AssemblyAI provider.

## 6. Success Criteria
- [ ] Toggling `enable_diarization = true` shows `[S1]` or `[S2]` in the HUD.
- [ ] Toggling it `false` returns to standard behavior (no labels).
- [ ] No regressions in OpenAI provider or standard AssemblyAI transcription.
