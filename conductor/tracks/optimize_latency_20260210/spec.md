# Specification: High-Performance Text Injection & Latency Reduction

## 1. Overview
The current text injection method (simulating key presses with sleeps) is too slow for real-time use, causing significant lag (up to 15s) and text truncation. We will replace it with a bulk injection method and optimize the `AppCoordinator` callback logic to ensure minimal latency between transcription and typing.

## 2. Functional Requirements

### 2.1. Bulk Text Injection
- **Replace keybd_event Loop:** Remove the per-character loop in `engine/injector.py`.
- **Implement SendInput (Unicode):** Use the Windows `SendInput` API via `ctypes` to inject entire strings in one go.
- **Async Execution:** Ensure injection remains non-blocking for the main event loop.

### 2.2. Callback Optimization
- **Streamline on_partial/on_final:** Ensure that transcription results are handed off to the injector with zero unnecessary buffering or delays.
- **Latency Instrumentation:** Add high-precision timestamps (Level 2 DEBUG) to track a packet from "Provider Received" -> "Coordinator Callback" -> "Injector Start" -> "Injector End".

## 3. Acceptance Criteria
- 100 characters of text are injected into a text box in < 200ms.
- The 15s lag between speaking and typing is eliminated (reduced to provider network latency only).
- No text truncation occurs due to overlapping injections (managed via the existing lock).
