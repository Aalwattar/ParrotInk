# Product Guidelines

## 1. Core Principles
- **Efficiency:** The application must be lightweight and have minimal impact on system resources.
- **Reliability:** The voice-to-text transcription must be accurate and dependable, with graceful handling of API errors or connectivity issues.
- **Intuitiveness:** The user interface, primarily through a tray icon and hotkeys, should be simple and require no learning curve.

## 2. Tone and Voice
- **Communication:** All user-facing text (tooltips, notifications, error messages) will be clear, concise, and professional.
- **Persona:** The application should feel like a silent, helpful assistant. It only acts when invoked and provides no unnecessary distractions.

## 3. Visual Identity
- **UI:** The primary interface is a system tray icon. There will be no main application window.
- **Iconography:** The tray icon must clearly communicate the application's state:
    - **Idle/Ready:** A standard, neutral icon.
    - **Listening:** A distinct visual indicator (e.g., a microphone symbol or a change in color) to show that audio is being captured.
    - **Error:** An indicator (e.g., a red dot or an exclamation mark) to signal a problem with the API key or connection.
- **Configuration:** A simple configuration window can be accessed from the tray menu for setting up API keys, hotkeys, and other options. This window should be clean and functional.

## 4. Messaging
- **Success:** No explicit success message is needed. The successful injection of text is its own confirmation.
- **Errors:** Error messages will be delivered via non-intrusive system notifications (e.g., a toast notification) and should be actionable (e.g., "Invalid OpenAI API Key. Please check your settings.").
- **Updates:** If update-checking functionality is added, it will be opt-in and notifications will be minimal.
