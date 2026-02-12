# Specification: Real-Time AssemblyAI & Smart Interaction Fix

## 1. Overview
This track addresses the 7-second latency in AssemblyAI by enabling immediate partial injections with "Smart Overwrite" (Backspace + Re-type) and fixes the reliable "any key" stop mechanism for Toggle mode.

## 2. Functional Requirements

### 2.1. Smart Partial Injection (AssemblyAI & OpenAI)
- **Immediate Handoff:** Pass all `Turn` updates (even if `end_of_turn: false`) to the `AppCoordinator` immediately.
- **Smart Overwrite Logic:**
    - The `AppCoordinator` will track the current `last_partial_text` length.
    - If a new partial arrives that is *different* from the old one (e.g., correction), the injector will:
        1. Send `N` Backspaces (where `N` is the length of `last_partial_text`).
        2. Type the entire new partial string.
    - If the new partial just *appends* to the old one, only type the new characters (efficient).
- **Finalization:** When `on_final` arrives, perform a final synchronization and reset the partial state.

### 2.2. Robust Toggle Mode Cancellation
- **Any-Key-Stop:** Ensure that in Toggle mode, *any* key press (excluding the initial release of the hotkey components) triggers `stop_listening`.
- **Performance Fix:** Ensure that `-vv` logging does not block the interaction thread or event loop, preventing the app from missing stop signals.

## 3. Acceptance Criteria
- AssemblyAI text appears on screen < 500ms after speech starts.
- Word corrections (e.g., "test" -> "testing") are visually corrected at the cursor via backspaces.
- Pressing *any* key (e.g., Space, Esc, Shift) immediately stops a Toggle mode session.
- No text duplication or truncation occurs during the "Smart Overwrite" process.
