# Specification: Explicit Provider Audio Contracts & Resampling (Track 2)

## Overview
Standardize the audio interface between the capture system and transcription providers. This track introduces a `ProviderAudioSpec` and an `AudioAdapter` layer to handle provider-specific transformations, including PCM16 conversion, high-quality resampling, and wire-format framing.

## Functional Requirements

### 1. Provider Audio Specification (`ProviderAudioSpec`)
- Define a structured contract for each provider:
    - `sample_rate_hz`: (e.g., 16000 for AssemblyAI, 24000 for OpenAI).
    - `channels`: (fixed to 1/mono).
    - `bit_depth`: (fixed to 16-bit).
    - `wire_encoding`: (`pcm16_bytes` or `pcm16_base64`).
    - `preferred_chunk_ms`: (e.g., 50ms or 100ms).

### 2. Audio Adapter Layer
- Create `AudioAdapter` to transform capture data into provider-ready data.
- **Responsibilities:**
    - **PCM16 Conversion:** Scale float input (`* 32767`) and clip to `int16` range.
    - **Resampling:** Use `python-soxr` for high-quality conversion (e.g., 16k to 24k).
    - **Stateful Resampling:** Reuse `soxr` resampler objects across the session.
    - **Wire Encoding & Framing:** Convert to `wire_encoding` and handle any required provider framing.
    - **Batching:** Buffer/split chunks to meet `preferred_chunk_ms`.

### 3. Provider Refactoring
- Update providers to declare their `ProviderAudioSpec`.
- Providers receive already-compliant data; they should not perform resampling or format conversion.

## Non-Functional Requirements
- **Audio Quality:** Use `soxr` to prevent aliasing.
- **Performance:** Avoid normalizing twice; the adapter is the final stage before the wire.

## Acceptance Criteria
- [ ] `python-soxr` dependency added.
- [ ] `AudioAdapter` converts 16kHz capture to 24kHz OpenAI-ready data with high fidelity.
- [ ] Providers no longer contain transformation logic.
- [ ] Unit tests verify PCM16 conversion, resampling accuracy, and wire-encoding.
