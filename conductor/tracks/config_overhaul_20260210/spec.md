# Specification: Granular Provider Configuration & AssemblyAI V3

## 1. Overview
This feature track overhauls the configuration system to support granular, provider-specific settings for OpenAI and AssemblyAI. It transitions AssemblyAI to the Streaming API V3 and reorganizes the `config.toml` structure into "core" and "advanced" sections for better usability.

## 2. Functional Requirements

### 2.1 Configuration Schema Update
-   **Structure:** The configuration file will use a hierarchical structure:
    ```toml
    [providers.openai.core]
    # Essential settings (URL, model, language)
    [providers.openai.advanced]
    # Tuning (VAD, noise reduction, timeouts)

    [providers.assemblyai.core]
    # Essential settings (V3 URL, sample rate, model)
    [providers.assemblyai.advanced]
    # Tuning (End-of-turn thresholds, formatting)
    ```
-   **Audio Section:** Introduce a global `[audio]` section to control microphone capture parameters (`capture_sample_rate`, `chunk_ms`).
-   **Legacy Removal:** The old `[advanced]` section containing raw URL overrides is removed.

### 2.2 Provider Updates
-   **OpenAI Provider:**
    -   Construct the WebSocket URL dynamically using `realtime_ws_url_base`, `realtime_ws_model`, and `transcription_model`.
    -   Apply advanced settings (VAD thresholds, silence duration) to the session initialization payload.
-   **AssemblyAI Provider:**
    -   **Upgrade to V3:** Update the WebSocket connection logic to use `wss://streaming.assemblyai.com/v3/ws`.
    -   **Parameter Mapping:** Map config values to V3 query parameters:
        -   `sample_rate` -> `sample_rate`
        -   `word_boost` -> `word_boost`
        -   `speech_model` -> `speech_model`
        -   `encoding` -> `encoding` (default `pcm_s16le`)
        -   `vad_threshold` -> `end_of_turn_confidence_threshold`

### 2.3 Configuration Loading
-   Update `engine/config.py` to use Pydantic models that reflect this new nested structure.
-   "Core" and "Advanced" fields should be merged or accessible seamlessly by the provider classes.

## 3. Technical Requirements
-   **AssemblyAI V3:** Ensure the URL builder handles V3-specific query parameters correctly.
-   **Validation:** Use Pydantic to validate that required "core" fields are present.
-   **Defaults:** `config.example.toml` must map 1:1 with the default values defined in the Pydantic models.

## 4. Acceptance Criteria
1.  **OpenAI:** The app connects successfully using settings read from `[providers.openai.core]`.
2.  **AssemblyAI:** The app connects to the **V3** endpoint (`wss://streaming.assemblyai.com/v3/ws`) and respects parameters like `word_boost` and `speech_model`.
3.  **Audio:** Changing `chunk_ms` in the config alters the audio chunk size sent to the provider.
4.  **Legacy:** The app starts without error if the old `[advanced]` section is missing (clean break).
5.  **Example:** A new `config.example.toml` exists with the fully commented, new structure.

## 5. Out of Scope
-   UI changes to the system tray menu.
-   Runtime reloading of the config (app restart required).
