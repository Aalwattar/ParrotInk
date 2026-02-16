# Track Spec: HUD & Status Synchronization

## Objective
Ensure that the floating HUD and the system tray status are perfectly synchronized with the application state, especially during provider switches, hotkey changes, and mode toggles.

## Current Issues
1. **HUD Desync**: The HUD may not update its visual state (like provider name or connection status) immediately when changed via the tray menu.
2. **Status Lag**: The tray icon tooltip and HUD status messages can get out of sync during fast transitions (e.g., STARTING -> CONNECTING -> LISTENING).
3. **Stale HUD Text**: Finalized text might linger on the HUD when it should be cleared for a new session.

## Success Criteria
- [ ] Provider name on HUD updates immediately when switched in Tray.
- [ ] Tray tooltip and HUD status labels always match.
- [ ] HUD correctly clears/resets state when a new dictation session starts.
- [ ] No race conditions in the `UIBridge` queue causing out-of-order status updates.

## Safety Constraints (CRITICAL)
- **NO UI OBSERVERS**: Under no circumstances should `IndicatorWindow` or `TrayApp` be registered as a `Config` observer. All visual updates MUST flow through the `UIBridge` queue to prevent deadlocks.
- **Thread Ownership**: All Win32/GDI+ calls must remain isolated within the UI polling thread.
