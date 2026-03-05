# Product Guidelines

## 1. Core Principles
- **Efficiency:** The application must be lightweight and have minimal impact on system resources.
- **Reliability:** The voice-to-text transcription must be accurate and dependable, with graceful handling of API errors or connectivity issues.
- **Intuitiveness:** The user interface, primarily through a tray icon and hotkeys, should be simple and require no learning curve.

## 2. Tone and Voice
- **Communication:** All user-facing text (tooltips, notifications, error messages) will be clear, concise, and professional.
- **Persona:** The application should feel like a silent, helpful assistant. It only acts when invoked and provides no unnecessary distractions.

## 3. Visual Identity & UX
- **UI:** The primary interface is a system tray icon. There will be no main application window.
- **Iconography:** The tray icon uses a "Modern Square" design with soft rounded corners.
    - **Idle:** Neutral Slate color (#475569).
    - **Listening:** Vibrant Microsoft Blue (#0078D4).
    - **Error:** Alert Red (#EF4444).
- **HUD:** The floating HUD provides real-time feedback using **Segoe UI 16pt** typography on an acrylic glass background, adhering to Windows modern design patterns.
- **Configuration:** A simple configuration window can be accessed from the tray menu for setting up API keys, hotkeys, and other options. This window should be clean and functional.

## 4. Messaging
- **Success:** No explicit success message is needed. The successful injection of text is its own confirmation.
- **Startup:** A non-intrusive "Ready" toast notification confirms successful launch and active hotkey.
- **Soft Errors:** Non-critical issues (e.g., network timeout) are delivered via non-intrusive HUD messages.
- **Critical Hardware Errors:** Major hardware or privacy blocks trigger a high-visibility, native Windows popup to ensure user awareness and provide immediate recovery steps.
- **Updates:** Update notifications are minimal and non-intrusive, appearing as a clickable status in the tray menu rather than a popup dialog.
