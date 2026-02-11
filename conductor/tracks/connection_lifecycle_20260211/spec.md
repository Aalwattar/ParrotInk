# Specification: Connection Lifecycle & Warm Connections (Track 4)

## Overview
Implement a flexible connection management system to optimize responsiveness and resource usage. This track introduces "Warm Connections" tied to the lifecycle of the listening state.

## Functional Requirements

### 1. Configuration
- `connection_mode`: `on_demand`, `warm` (Default), or `always_on`.
- `warm_idle_timeout_seconds`: (Default: 300, Range: 30-1800).

### 2. Connection Logic (`ensure_connected`)
- Implement idempotent `ensure_connected()` called at the start of every `start_listening()`.

### 3. Idle Timer & Activity Definition
- The idle timer starts immediately upon `stop_listening()`.
- **Implementation:** Use monotonic timestamps + a single delayed check task to avoid cancel-race bugs.
- Any subsequent `start_listening()` resets the timestamp, causing the delayed task to skip closure.
- **Logging:** Log warm closure at `INFO` (rate-limited).

### 4. Reconnection & Session Rotation
- **Lazy Reconnect:** Reconnect only on the next `start_listening()`.
- **Backoff:** Apply exponential backoff only when `ensure_connected()` fails.
- **Session Rotation (OpenAI):** Enforce 55-minute max age.
- **Rotation Guard:**
    - Never rotate while `state == LISTENING`.
    - If max age reached while `LISTENING`, set `rotation_pending` flag and rotate immediately after `stop_listening()`.

## Non-Functional Requirements
- **Strict Data Invariant:** No audio is sent to the provider unless `state == LISTENING` (no `send_audio` in `IDLE` or `WARM_CONNECTED`).

## Acceptance Criteria
- [ ] Warm connections persist across sessions and reconnect lazily if dropped.
- [ ] Idle timer closes connection after specified timeout.
- [ ] **Verification:** No audio sent unless `state == LISTENING`.
- [ ] Session rotation Guard prevents mid-dictation drops.
- [ ] Unit tests verify rotation guard and timer logic.
