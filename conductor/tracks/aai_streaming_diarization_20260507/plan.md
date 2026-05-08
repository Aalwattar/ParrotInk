# AssemblyAI Streaming Diarization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement real-time speaker labeling for AssemblyAI using word-level labels and a modular "Compact" visual style.

**Architecture:** Add a toggle in the configuration, update the URL resolver to request speaker labels, and introduce a `SpeakerManager` class to isolate the formatting logic before text is sent to the HUD.

**Tech Stack:** Python, Pydantic, AssemblyAI Streaming V3 (WebSocket), Pytest.

---

### Task 1: Update Configuration Schema

**Files:**
- Modify: `engine/config.py:223-228`
- Modify: `engine/app_types.py:53-56`
- Modify: `engine/config_resolver.py:141-155`

- [ ] **Step 1: Add `enable_diarization` to `AssemblyAIAdvancedConfig`**

```python
# engine/config.py around L223
class AssemblyAIAdvancedConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    override: bool = False
    format_text: bool = False
    enable_diarization: bool = False  # Add this line
    keyterms_prompt: List[str] = Field(default_factory=list)
```

- [ ] **Step 2: Add `enable_diarization` to `EffectiveAssemblyAIConfig`**

```python
# engine/app_types.py around L53
@dataclass(frozen=True)
class EffectiveAssemblyAIConfig:
    # ... existing fields ...
    format_text: bool
    enable_diarization: bool  # Add this line
    stop_timeout: float
    is_test: bool
```

- [ ] **Step 3: Update `resolve_effective_config` to include the new toggle**

```python
# engine/config_resolver.py around L141
    resolved_aai = EffectiveAssemblyAIConfig(
        # ...
        format_text=aai_adv.format_text,
        enable_diarization=aai_adv.enable_diarization, # Add this line
        stop_timeout=config.audio.provider_stop_timeout_seconds,
        is_test=config.test.enabled,
    )
```

- [ ] **Step 4: Update WS URL generation to include `speaker_labels=true`**

```python
# engine/config_resolver.py around L116
    if aai_adv.format_text:
        params["format_turns"] = "true"

    if aai_adv.enable_diarization:
        params["speaker_labels"] = "true" # Add this block
```

- [ ] **Step 5: Run tests to ensure config still validates**

Run: `pytest tests/test_config.py -v`
Expected: PASS

### Task 2: Implement SpeakerManager

**Files:**
- Create: `engine/transcription/speaker_manager.py`
- Test: `tests/test_speaker_manager.py`

- [ ] **Step 1: Write unit tests for SpeakerManager**

```python
import pytest
from engine.transcription.speaker_manager import SpeakerManager

def test_speaker_manager_formats_compact():
    sm = SpeakerManager()
    words = [{"text": "Hello", "speaker": 1}, {"text": "world", "speaker": 1}]
    formatted = sm.format_with_speaker(words, "Hello world")
    assert formatted == "[S1] Hello world"

def test_speaker_manager_tracks_speaker_change():
    sm = SpeakerManager()
    words1 = [{"text": "Hello", "speaker": 1}]
    assert sm.format_with_speaker(words1, "Hello") == "[S1] Hello"

    words2 = [{"text": "Hi", "speaker": 2}]
    assert sm.format_with_speaker(words2, "Hi") == "[S2] Hi"
```

- [ ] **Step 2: Create `SpeakerManager` class**

```python
from typing import List, Dict, Any, Optional

class SpeakerManager:
    """Manages speaker labels for streaming transcription."""
    def __init__(self):
        self.current_speaker: Optional[int] = None

    def format_with_speaker(self, words: List[Dict[str, Any]], transcript: str) -> str:
        if not words:
            return transcript

        # AssemblyAI Major Upgrade: each word has its own speaker label.
        # We take the speaker from the first word of the segment.
        speaker = words[0].get("speaker")
        if speaker is None:
            return transcript

        self.current_speaker = speaker
        return f"[S{speaker}] {transcript}"
```

- [ ] **Step 3: Run unit tests**

Run: `pytest tests/test_speaker_manager.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add engine/transcription/speaker_manager.py tests/test_speaker_manager.py
git commit -m "feat(aai): add SpeakerManager for modular diarization formatting"
```

### Task 3: Integrate with AssemblyAIProvider

**Files:**
- Modify: `engine/transcription/assemblyai_provider.py`

- [ ] **Step 1: Initialize SpeakerManager in `__init__`**

```python
# engine/transcription/assemblyai_provider.py
from .speaker_manager import SpeakerManager # Add import

# In __init__:
self.speaker_manager = SpeakerManager() if effective_config.enable_diarization else None
```

- [ ] **Step 2: Update `_handle_event` to use the manager**

```python
# engine/transcription/assemblyai_provider.py around L148
        if text is not None:
            words = event.get("words", [])
            if self.speaker_manager and words:
                text = self.speaker_manager.format_with_speaker(words, text)

            if msg_type == "Turn":
                # ... rest of logic uses the updated 'text'
```

- [ ] **Step 3: Commit**

```bash
git add engine/transcription/assemblyai_provider.py
git commit -m "feat(aai): integrate SpeakerManager into AssemblyAIProvider"
```

### Task 4: Definition of Done (DOD) Gate

- [ ] **Step 1: Run Linting**

Run: `uv run ruff check .`
Expected: No errors

- [ ] **Step 2: Run Formatting Check**

Run: `uv run ruff format --check .`
Expected: No errors

- [ ] **Step 3: Run Type Checking**

Run: `uv run mypy .`
Expected: Success: no issues found

- [ ] **Step 4: Run All Tests**

Run: `uv run pytest -q`
Expected: All tests pass (including new speaker manager tests)

- [ ] **Step 5: Lock and Sync**

Run: `uv lock; uv sync --locked`
Expected: Lockfile updated and env synced.

- [ ] **Step 6: Final Commit**

```bash
git add .
git commit -m "chore: final verification and lockfile update for diarization feature"
```
