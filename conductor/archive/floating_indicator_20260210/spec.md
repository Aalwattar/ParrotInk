# Specification: Floating Recording Indicator

## 1. Overview
This feature introduces a small, "Win+H" inspired floating visual indicator that reflects the current dictation state. Unlike the tray icon, which might be hidden or distant, this indicator provides immediate, in-context feedback. It is purely informational (non-clickable for control) and designed to be subtle and non-disruptive.

## 2. Functional Requirements

### 2.1 Visual Appearance
- **Design:** A small, border-less circular or pill-shaped window.
- **States:**
  - **Idle:** Semi-transparent and subtle (e.g., dim gray or black ring).
  - **Recording:** Animate a "pulse" effect with a red glow or ring to indicate active capture.
- **Topmost:** The window must stay "Always on Top" of other applications.

### 2.2 Behavior & Interaction
- **Draggable:** Users can click and drag the indicator to any position on the screen.
- **Persistence:** The application must remember the X/Y coordinates of the indicator across restarts.
- **Non-Interactive:** Clicks (other than for dragging) pass through or are ignored; it does not trigger dictation start/stop.

### 2.3 Configuration
- New configuration section in `config.toml`:
  ```toml
  [ui.floating_indicator]
  enabled = true
  opacity_idle = 0.3
  opacity_active = 0.8
  initial_x = 500
  initial_y = 50
  ```

## 3. Implementation Details
- **Framework:** Python **Tkinter** (built-in).
- **Window Management:** Use `overrideredirect(True)` for a border-less look and `wm_attributes("-topmost", True)` for visibility.
- **Animation:** Use Tkinter's `.after()` loop to create the pulsing effect by varying the opacity or drawing size of the recording ring.

## 4. Acceptance Criteria
1. **Visual Feedback:** When recording starts, the indicator immediately begins its "pulse" animation.
2. **Subtlety:** The indicator is small and doesn't obscure significant portions of the screen.
3. **Draggability:** The user can move the indicator, and it stays in the new position until moved again.
4. **Persistence:** Closing and reopening the app restores the indicator to its last dragged position.
5. **No Interference:** The indicator does not steal focus or prevent clicking on items behind its semi-transparent areas (where possible with Tkinter).
