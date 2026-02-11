# Specification: Audio Pipeline Optimization (Track 1)

## Overview
Refactor the audio capture pipeline to replace the current thread-polling mechanism with an event-driven `asyncio.Queue`. This change aims to reduce CPU overhead, eliminate jitter, and enforce "cheap and universal" audio data invariants at the capture boundary.

## Functional Requirements

### 1. Event-Driven Capture
- **Queue Implementation:** Replace the existing `queue.Queue` bridging with a bounded `asyncio.Queue(maxsize=100)`.
- **Thread-to-Loop Bridge:** Use `loop.call_soon_threadsafe(async_q.put_nowait, chunk)` within the `sounddevice` callback to push data into the async queue.
- **Overflow Policy:** Implement a "Drop Oldest" policy. If the queue is full:
    - Perform a `get_nowait()` to remove the oldest chunk.
    - Perform a `put_nowait()` to insert the new chunk.
    - Track and log dropped chunks (rate-limited to once per second).

### 2. Capture Boundary Invariants
Enforce "cheap" universal invariants immediately at the capture boundary to prevent stereo or invalid data from leaking into the async pipeline.
- **Downmixing:** If the input device provides stereo `(N, 2)`, automatically downmix to mono by averaging channels before reshaping.
- **Reshaping:** Automatically flatten `(N, 1)` to `(N,)`.
- **Validation:** 
    - Reject non-numeric data or data with `ndim > 2` (raise `CaptureFormatError`).
    - Sanitize `NaN` or `Inf` values in float input by replacing them with `0`.
- **Note:** Conversion to `int16` and resampling are deferred to the Provider Adapter (Track 2).

### 3. Resilience and Error Handling
- **Loop Availability:** If `loop.call_soon_threadsafe` fails (e.g., during shutdown):
    - Increment a failure counter.
    - Emit a rate-limited UI/Console warning: *"Audio capture dropping chunks: event loop unavailable (shutdown in progress)"*.
- **Automatic Stop:** If failures exceed a threshold (e.g., 10 consecutive failures or >100 in 1 second), set a `stop_capture` flag to halt the `sounddevice` stream.

## Non-Functional Requirements
- **Efficiency:** Eliminate `get_nowait() + sleep()` polling to reduce idle CPU consumption.
- **Latency:** Reduce jitter by ensuring the event loop is notified immediately upon chunk availability.

## Acceptance Criteria
- [ ] No polling logic (`sleep`) exists in the audio streaming generator.
- [ ] Memory usage remains bounded even if the provider consumer stalls.
- [ ] Audio callback thread never blocks under any queue condition.
- [ ] Stereo input is automatically downmixed to Mono-1D at the capture boundary.
- [ ] Unit tests verify downmixing, reshaping, and NaN sanitization.
