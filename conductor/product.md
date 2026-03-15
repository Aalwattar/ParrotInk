# Product Definition

## 1. Initial Concept

The user wants to build a real-time voice-to-text application for Windows. It should use online transcription APIs (OpenAI and AssemblyAI) and inject the resulting text at the user's current cursor position. The application should be configurable and run as a system tray utility.

## 2. Core Features

### 2.1. Real-time Transcription
- The application will capture audio from the user's microphone and stream it to a selected online transcription service in real-time.
- It must handle and display both partial (interim) and final transcription results.

### 2.2. API Provider Support
- **OpenAI:** Integrate with OpenAI's real-time transcription service.
- **AssemblyAI:** Integrate with AssemblyAI's real-time transcription service.
- The user can select the desired provider through the application's settings.

### 2.3 Hotkey Control
- **Unified Hotkey:** The application uses a single configurable hotkey for control.
- **Smart Interaction:** The hotkey serves as the "Start" trigger. Once active, **any** keyboard interaction (including the hotkey itself or modifiers) acts as a "Stop" command.
- **Manual Priority:** To prevent AI interference with manual typing, if a session is stopped by a key press, any pending transcription text is discarded. The user's manual input always takes precedence.

### 2.4 Text Injection
- The primary function is to inject the final transcribed text directly at the current text cursor's location in the active application.
- The injection should simulate keyboard typing to ensure broad compatibility.

### 2.5 System Tray Application
- The application will run as a background process with an icon in the system tray.
- **Professional Identity:** The tray icon uses high-quality, custom `.ico` assets to provide a polished, "Fluent" visual identity on Windows.
- **Visual Feedback:** The icon changes based on state: Idle, Listening, Connecting, Error, and Transition. If assets are missing, the system automatically falls back to a robust, color-coded dynamic square generation (Grey, Blue, Yellow, Red).
- A redesigned context menu on the tray icon allows the user to:
    - **Dynamic Version Header:** Displays the current version and update status (Top-level).
    - **Transcription Sub-menu:** Select active Provider and Microphone Profile.
    - **Settings Sub-menu:** Configure hotkeys, "Hold to Talk" mode, and Audio Feedback.
    - **Tools Sub-menu:** Access Statistics dashboard, open config/log folders, and reload settings.
    - **Help Sub-menu:** View documentation, report issues, and check for updates manually.
    - **Quit:** Exit the application.

### 2.6. Configuration
- All settings will be managed through a local configuration file in TOML format for easy editing.
- Configurable options will include:
    - API provider selection, API keys, and **Test Mode** toggle.
    - **Secure Credential Management:** API keys are stored securely in the Windows Credential Manager and never saved in plain text configuration files.
    - **Smart UI Validation:** Providers are automatically disabled (grayed out) in the system tray if their required credentials are missing, unless in Test Mode. If exactly one provider has a valid key, the application automatically selects it to streamline onboarding.
    - **Smart Provider Auto-Selection:** If the current provider lacks an API key but another provider is configured, the application automatically switches the active provider. This happens at startup and dynamically whenever keys are updated.
    - **User-Friendly Profiles:** High-level `latency_profile` (fast, balanced, accurate) and `mic_profile` (headset, laptop, none) simplify complex engineering parameters. `headset` is the default to ensure high accuracy with noise reduction enabled.
    - **Granular Advanced Settings:** Power users can still override profiles to fine-tune VAD thresholds, models, and silence durations.
    - **Configuration Fidelity:** All engine parameters are exposed and respected. Programmatic saves (via UI) utilize style-preserving TOML to ensure all user comments and document structure are maintained.
    - **AssemblyAI V3 Integration:** Leverages the latest AssemblyAI Streaming V3 API for improved performance and more detailed session control.
    - **Verbose Debugging & Structured Logging:** Multi-level, non-blocking logging to console and file, with automatic redaction of secrets and truncation of audio data.
    - **Interactive Hotkey Setup:** Users can record their desired hotkey combination directly through a tray-driven recording dialog.
    - **Diagnostics:** A new `app config --explain` CLI command provides a clear report of how high-level profiles map to specific technical timings and thresholds.
    - **Live Configuration Refresh:** The application supports an in-place reload mechanism that validates and applies manual edits to the `config.toml` file without requiring a process restart. This now includes dynamic logging updates, allowing users to toggle verbosity (e.g., from ERROR to DEBUG) instantly.
    - **Hold to Talk:** A toggle in the Tray menu to switch between "Hold to Talk" and "Smart Toggle" modes.
    - **Hardened Security:** The application strictly validates transcription provider URLs against a hardcoded list of trusted domains. This prevents "Silent Key Theft" by refusing to connect to unauthorized custom endpoints defined in the configuration file.
    - **Optimized Connection Management:** Transcription provider connections are managed with a graceful 7.0-second shutdown timeout, significantly reducing lag and ensuring reliable session finalization.
    - **Advanced Configuration:** Power users can still provide custom API endpoints (URLs) for transcription providers to support local mock servers, provided they adhere to the application's strict domain trust policies.
    - Transcription language.

    ### 2.8. Headless Evaluation Mode
    - A dedicated CLI mode (`eval`) for deterministic accuracy testing and regression monitoring.
    - Replays WAV files through the existing transcription pipeline without triggering UI, text injection, or audio feedback.
    - Produces structured JSON output containing transcription results and performance metrics (latency, final text).

    ### 2.7. Tray Interaction
    - **Provider Selection:** Users can switch between providers directly from the tray menu.
    - **Visual Feedback:** The app indicates its state (Idle, Listening, Error) through the tray icon color.
    - **Dynamic Menu:** The "Default Provider" setting from the config determines the initial selection, and availability is checked dynamically.
    - Custom word overrides or vocabulary lists to improve accuracy.
    - Simple post-processing rules for the transcribed text.

    ### 2.9. Distribution
    - **Standard Installer (Recommended):** The primary distribution method is a professional Inno Setup installer (`ParrotInk-Setup.exe`). It installs to `%LOCALAPPDATA%\ParrotInk`, handles clean auto-updates (stopping running instances), and manages system shortcuts.
    - **Seamless Background Updates:** The application features a Windows-native update manager that leverages the Background Intelligent Transfer Service (BITS) to download new versions silently in the background. It verifies updates via SHA256 checksums and provides interactive installation prompts.
    - **Portable Executable:** A standalone `ParrotInk.exe` remains available for advanced or temporary use, with the caveat that moving the file after setup may break "Run at Startup" functionality.
    - **Portable Paths:** When running as an EXE, the application correctly resolves configuration and log files to the user's `%APPDATA%\ParrotInk` directory, ensuring it works even when launched from read-only locations.
    - **Single Instance Protection:** The application uses a Win32 Mutex to ensure only one instance is running at a time, preventing hotkey and microphone conflicts. If a second instance is launched, it displays a helpful notification and exits gracefully.
    - **Automation-Friendly:** A `--background` CLI flag allows the application to start silently without the "already running" warning, ideal for startup scripts and automation.

    ### 2.10 Visual Feedback & HUD
    - **Acrylic HUD:** A floating, minimalist "Acrylic" indicator appears during recording to show live transcription progress.
    - **RTL & Arabic Support:** The HUD correctly handles Right-to-Left (RTL) text and Arabic character shaping, ensuring high-fidelity rendering for diverse languages.
    - **Startup Robustness:** The HUD features built-in recovery logic with automated retries and health monitoring. If it fails to initialize during system startup or crashes unexpectedly, it can automatically re-initialize or be recovered manually by toggling its display in the tray menu.
    - **Persistent Error HUD:** Critical hardware and privacy error messages persist on the HUD until resolved, ensuring the user doesn't miss important actionable feedback.
    - **Startup Confirmation:** A native Windows toast notification appears when the application starts (unless launched with `--background`), confirming readiness and reminding the user of their configured hotkey.
    - **Modern Typography:** The HUD uses the Windows system font (**Segoe UI**) at a high-readability size (16pt) for a professional, integrated look.
    - **Dynamic Status:** The HUD indicator pulses or changes color based on voice activity and finalization state.
    - **Integrated Branding:** The active provider name (e.g., "OpenAI", "AssemblyAI") is displayed directly on the HUD for immediate context.

    ### 2.11 Usage Statistics
    - **Persistent Tracking:** The application automatically tracks key usage metrics, including total transcriptions, cumulative duration, word count, and error rates.
    - **Provider Breakdown:** Usage is tracked per transcription provider to help users understand their utilization of different services.
    - **Modern Dashboard:** A "Statistics" menu item in the system tray opens a professional, instant-launch dashboard (using `ttkbootstrap`) that aggregates data for Today, This Week, This Month, and Lifetime.
    - **Data Sovereignty:** All statistics are stored locally in a `stats.json` file within the user's `%APPDATA%\ParrotInk` directory and never transmitted to external servers.

    ### 2.12. Hardware Diagnostics & Privacy
    - **Surgical Diagnostics:** The application performs OS-level checks for microphone privacy blocks and hardware availability *before* attempting any network connections, preventing log spam and timeouts.
    - **Interactive Recovery:** If a microphone block is detected, a native Windows popup provides clear instructions on enabling the "Let desktop apps access your microphone" toggle in Windows Settings.
    - **Deep Linking:** Tray menu "FIX" links and popup buttons take the user directly to the relevant Windows 11 Privacy & security page.

    ### 2.13 Automatic Update Checking
    - **GitHub Integration:** The application automatically checks for newer releases on GitHub at startup and every 24 hours.
    - **Non-Intrusive:** Notifications are integrated directly into the tray menu's version label to avoid interrupting the user's workflow.
    - **Rate-Limit Aware:** The system respects GitHub API rate limits and handles offline states or API errors gracefully.

    ### 2.14 CI/CD & Automation
    - **Automated Quality Gate:** A GitHub Actions CI workflow automatically runs linters (Ruff), type checkers (Mypy), and unit tests (Pytest) on every push to `main` and all pull requests.
    - **Automated Releases:** A dedicated Release workflow builds the standalone Windows executable and creates a GitHub Release with version-verified assets (EXE and SHA256 checksum) whenever a new version tag (e.g., `v1.2.3`) is pushed.

    ### 2.15 First-Run Onboarding
    - **Welcome Popup:** A professional, dark-themed welcome window (using `ttkbootstrap`) appears automatically when the application is launched for the first time.
    - **Educational Content:** The popup introduces the system tray interaction model, explains the state-based color coding of the tray icon, and provides clear directions for adding API keys via the Settings menu.
    - **Configurable Suppression:** Users can choose to "Don't show this again," which permanently saves the preference to the configuration file. The popup is also automatically suppressed when the application is launched with the `--background` flag.
    - **Blocking Gatekeeper:** The onboarding window acts as a blocking modal before the main application logic starts, ensuring new users are properly oriented before the tray icon appears.

    ### 2.16. Audio Device Selection & Robustness
    - **Granular Device Control:** Users can select a specific microphone for audio capture by name or partial name in the configuration.
    - **Robust Fallbacks:** If a configured device is unavailable, the system automatically falls back to the system's default recording device.
    - **Communication Ducking Mitigation:** The application utilizes WASAPI Shared mode with automatic conversion to prevent Windows from aggressively lowering the volume of other applications (ducking) during active recording sessions.
    - **Responsive Initialization:** Audio stream initialization is performed in an isolated background thread, ensuring that hotkey triggers remain responsive even if the audio driver takes time to open.

### 3.1. Audio Pipeline
- **Audio Capture:** Use `sounddevice` for microphone input.
- **Encoding & Streaming:**
        - **OpenAI:** Audio must be resampled to 24kHz mono PCM and streamed.
        - **AssemblyAI:** Audio must be streamed over a secure WebSocket (WSS) using the **Streaming V3 API**, sending raw binary audio frames.
    - **Real-time Transport:** Use the `websockets` library for low-latency streaming.
     The application must gracefully handle connection errors and reconnect attempts.

### 3.2. Windows Integration
- **Hotkeys:** The preferred implementation is the `pywin32` library to register global system hotkeys for robustness. `pynput` is a viable alternative.
- **Text Injection:** Use `pywin32` to simulate `SendInput` events for seamless text injection. A fallback mechanism using the clipboard (preserving its original content) should be available.

### 3.3. Dependencies
- **Audio:** `sounddevice==0.5.5`
- **Networking:** `websockets==16.0`, `httpx==0.28.1`
- **API SDKs:** `openai==2.17.0`, `assemblyai==0.50.0`
- **Windows Integration:** `pywin32==311`, `pystray==0.19.5`
- **Hotkey Alternative:** `pynput==1.8.1`
