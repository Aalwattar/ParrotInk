# Specification: fix_provider_switch_delay_and_stutter

## Overview
Users experience a significant delay (approx. 20 seconds) and audio "stuttering" when switching transcription providers via the system tray. If a switch is initiated during an active dictation session, the start/stop sounds repeat multiple times and the HUD persists. During the transition delay, the application becomes unresponsive to the hotkey, though it eventually recovers once the switch completes.

## Functional Requirements
1. **Instant Session Termination:** If a provider switch is initiated during an active session, the current session must be cancelled immediately.
2. **HUD Cleanup:** The HUD must disappear immediately upon initiating a provider switch, regardless of the previous session state.
3. **Responsive Provider Switching:** The transition between providers (e.g., OpenAI to AssemblyAI) should be near-instant and non-blocking.
4. **Hotkey Safety:** The hotkey listener must either be correctly paused and resumed or remain responsive without causing a "hang" state during the provider transition.
5. **Silence the Stutter:** Prevent multiple start/stop feedback sounds from playing during the cleanup phase of a provider switch.

## Non-Functional Requirements
- **Stability:** The application must not enter an unresponsive state during configuration reloads.
- **Efficiency:** The disconnection logic for providers (especially OpenAI) must be optimized or moved to a non-blocking background task.

## Acceptance Criteria
- [ ] Switching providers while idle completes in under 2 seconds.
- [ ] Switching providers during active dictation immediately stops recording, plays the "stop" sound exactly once, and hides the HUD.
- [ ] The hotkey works immediately after the tray indicates the provider change is complete.
- [ ] No application "hangs" are observed when pressing the hotkey during or immediately after a switch.

## Out of Scope
- Changing the underlying transcription logic of the providers themselves.
- Modifying the tray UI design.
