# Specification: Floating Acrylic Recording Indicator

## Overview
Implement a modern, floating, and draggable recording indicator for the `parrotink` application. This indicator provides real-time visual feedback of the recording status and displays a short buffer of non-final (partial) transcription text in a sleek, Fluent-style interface.

## Functional Requirements
- **Draggable UI**: A floating window that can be moved anywhere on the screen by clicking and dragging.
- **Acrylic Design**: Use Win32 layered windows and composition (where available) to achieve a modern, semi-transparent blurred (Acrylic) look.
- **Status Visualization**:
    - **Idle**: Neutral translucent state.
    - **Recording**: Soft red glow/color transition on the background or border.
- **Partial Text Display**:
    - A "side-car" panel extending from the main icon.
    - Displays a short buffer of the last 3-5 words of the non-final transcription.
    - Translucent and unobtrusive.
- **Thread-Safety**: Integrated into the existing `UIBridge` / Tray event loop to ensure thread-safe communication with the transcription engine.

## Non-Functional Requirements
- **Responsiveness**: The indicator must remain fluid and responsive to drags.
- **Low Resource Usage**: Minimal CPU/GPU impact for the blur and transparency effects.
- **Win32 Native**: Built using `ctypes` and the Windows API to avoid large external UI dependencies.

## Acceptance Criteria
- [ ] Indicator window appears on startup or when toggled.
- [ ] Indicator can be dragged and its position is remembered (optional, but preferred).
- [ ] Background changes color smoothly when `start_listening` and `stop_listening` are triggered.
- [ ] Partial transcripts from OpenAI/AssemblyAI appear in the side-car panel in real-time.
- [ ] Side-car panel correctly manages a 3-5 word buffer (dropping older words).

## Out of Scope
- Complex animations (beyond basic transitions).
- Full transcription history in the floating window.
- Custom skinning/theming beyond the Acrylic baseline.
