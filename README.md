<p align="center">
  <img src="assets/icons/icon_128.png" width="128" alt="ParrotInk Logo">
</p>

# ParrotInk: Stop Typing. Start Thinking.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Latest Release](https://img.shields.io/github/v/release/Aalwattar/ParrotInk?sort=semver)](https://github.com/Aalwattar/ParrotInk/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)](https://www.microsoft.com/windows)

### High-accuracy, ultra-low latency real-time voice-to-text — Native for Windows.

You think faster than you type. **ParrotInk** closes that gap. It is the only open-source, Windows-native application that brings professional-grade, real-time voice-to-text directly to your cursor. With a polished visual identity and high-fidelity tray feedback, ParrotInk streams your words instantly so you never lose your flow state.

---

## Visual Preview

### Real-time English & RTL (Arabic) Support
ParrotInk natively handles mixed-language environments and Right-to-Left (RTL) text.

https://github.com/user-attachments/assets/f31a88ee-243b-42e8-9e18-32b55ad6ecfa

*(Note: Demonstration showing the real-time streaming, Skia-powered HUD with Acrylic blur, and RTL alignment.)*

---

## Download & Install

ParrotInk provides two ways to get started on Windows. We **highly recommend** the Standard Installer for the best experience, including automatic updates and stable shortcut management.

### 1. Standard Installer (Recommended)
The most robust way to use ParrotInk. It handles process management, clean updates, and ensures your Start Menu and Desktop shortcuts always point to the right place.

- **Download**: [ParrotInk-Setup.exe (Latest)](https://github.com/Aalwattar/ParrotInk/releases/latest/download/ParrotInk-Setup.exe)
- **Install Location**: `%LOCALAPPDATA%\ParrotInk` (No Administrator rights required).
- **Updates**: Simply run the new installer version to automatically stop the app and perform a clean upgrade.

### 2. Portable Executable (Advanced)
A single, standalone `ParrotInk.exe` with no installation required. Ideal for USB drives or temporary use.

- **Download**: [ParrotInk.exe (Latest)](https://github.com/Aalwattar/ParrotInk/releases/latest/download/ParrotInk.exe)
- **⚠️ Warning:** If you move the `.exe` file after enabling **Run at Startup**, Windows will be unable to find the application at the next boot. We recommend the Standard Installer if you plan to use this feature.

---

## Key Features

- **Zero-Latency Feel:** Real-time streaming ensures your text appears as you speak, keeping you in the zone.
- **Multi-Speaker Diarization:** Real-time speaker labeling (e.g., `[S1]`, `[S2]`), perfect for meetings and interviews.
- **Global Language Support:** Works with almost any language (English, Spanish, French, Chinese, Japanese, etc.) via world-class AI models.
- **Native RTL Support:** Full support for Arabic and other Right-to-Left languages with correct character shaping and HUD alignment.
- **Automatic Background Updates:** Downloads new versions silently in the background using Windows BITS.
- **Smart Injection:** Automatically stops recording if you start typing manually, preventing text collisions.
- **Secure by Design:** API keys are stored safely in the Windows Credential Manager.

---

## Table of Contents
- [Download & Install](#download--install)
- [Key Features](#key-features)
- [Getting Started](#getting-started)
- [Choose Your Engine](#choose-your-engine)
- [User Manual: How it Works](#user-manual-how-it-works)
- [Privacy & Security](#privacy--security)
- [The Story Behind ParrotInk](#the-story-behind-parrotink)
- [Customization & Advanced Settings](#customization--advanced-settings)
- [Building from Source](#building-from-source)
- [License](#license)

---

<details>
<summary><b>🚀 The Story Behind ParrotInk (Click to expand)</b></summary>

I built ParrotInk because existing dictation tools broke my concentration. They either forced me to wait for "batch processing" to dump a giant block of text onto the screen, or—like the built-in Windows dictation (`Win + H`)—struggled heavily with slight accents.

I wanted true real-time streaming with professional-grade accuracy, and I wanted the freedom to use my own API keys from industry leaders like OpenAI and AssemblyAI. When I couldn't find a single open-source, Windows-native tool that met these standards, I decided to build it. ParrotInk is the result: a tool designed for people who want to type as fast as they can think, without the wait.
</details>

---

## Getting Started

1.  **Launch**: Open `ParrotInk-Setup.exe` (or `ParrotInk.exe`).
2.  **Windows Security**:
    > Because ParrotInk is a new open-source project and is not yet signed with a paid Microsoft Developer certificate, you may see a "Windows protected your PC" warning.
    >
    > To run the app: Click **More info** -> **Run anyway**.
3.  **Setup API Key**:
    *   **What is an API Key?** A "secret password" that allows ParrotInk to securely talk to the AI models (OpenAI, AssemblyAI, or Cloudflare AI Gateway).
    *   **How to get one**: Sign up for a free account at [AssemblyAI](https://www.assemblyai.com/dashboard/) or [OpenAI](https://platform.openai.com/api-keys).
    *   **Where to put it**: Right-click the ParrotInk tray icon and select **Settings > API Credentials**.
4.  **Start Dictating**: Press `Ctrl + Alt + V` (default) and start speaking. Your words will appear instantly at your cursor!

---

## Choose Your Engine

ParrotInk supports direct OpenAI and AssemblyAI connections and Cloudflare AI Gateway. Stop dictation, then right-click the tray icon to select **Transcription > Provider** and **Transcription > Model**. Model choices come from the app's shared model catalog. Pending audio is finalized before the next model connection starts.

### AssemblyAI

The default model is **Universal 3.6 Pro Realtime** (`universal-3-6-pro`). It supports native multilingual recognition, vocabulary and conversation context, acoustic focus, and speaker labels.

- Use the response speed profile for `min_latency`, `balanced`, or `max_accuracy` operation.
- Set `language_codes` for expected languages, or leave it empty for multilingual recognition.
- Headset and laptop microphone profiles map to `near-field` and `far-field` Voice Focus. Explicit `voice_focus` settings override the profile.
- Advanced settings include recognition instructions, `agent_context`, and speaker labeling. Modern models return formatted turns directly.

The adapter waits for the server's `Begin` acknowledgement and finalizes the pending phrase when capture stops. See the [AssemblyAI streaming reference](https://www.assemblyai.com/docs/streaming/api-spec/streaming-websocket) and [release notes](https://www.assemblyai.com/changelog).

### OpenAI

The default model is **GPT Live Transcribe** (`gpt-live-transcribe`), which emits text while you speak. **GPT Transcribe** (`gpt-transcribe`) begins transcription after each committed phrase and is available in the Model menu.

Both modern models use local speech detection and explicit audio commits. ParrotInk commits after the configured silence interval or when you stop dictation, then waits for the final transcript. Transcript items are tracked separately and delivered in spoken order even if the server finishes them out of order.

Set `languages` for multilingual hints and use `prompt` and `keywords` for contextual vocabulary. The response speed profile maps to `delay = "low"`, `"medium"`, or `"high"`; advanced overrides allow all supported delay levels. Legacy GPT-4o transcription models remain supported through existing configurations but are hidden from the model menu. Their announced retirement date is February 26, 2027. See the [OpenAI realtime transcription guide](https://developers.openai.com/api/docs/guides/realtime-transcription) and [deprecation schedule](https://developers.openai.com/api/docs/deprecations).

The OpenAI and AssemblyAI model menus show the two current models for each provider. Older models can still be selected in TOML. The installer bundles the configuration template for first launch; upgrades preserve your existing file, and missing settings use application defaults.

### Cloudflare AI Gateway

Cloudflare is a connection route to supported speech models, including Cloudflare-hosted models and third-party xAI models. The app currently supports:

| Model | Behavior |
| --- | --- |
| `@cf/deepgram/nova-3` (default) | Cloudflare-hosted streaming transcription with interim and final results. |
| `@cf/deepgram/flux` | Cloudflare-hosted streaming transcription with turn events. |
| `xai/grok-stt` | Grok speech-to-text through Cloudflare's unified streaming endpoint. |

To configure it:

1. Create an AI Gateway in your [Cloudflare dashboard](https://dash.cloudflare.com/) and obtain an API token with access to the gateway and selected model service.
2. Open **Settings > Configure Cloudflare Gateway...** from the tray. Enter your **Account ID**, **Gateway ID**, selected **Transcription model**, and **API token**. You can also set the token through **Settings > API Credentials > Set Cloudflare API Token...**.
3. Give the token **Account > AI Gateway > Run** for hosted Nova-3/Flux and **Account > Workers AI > Read** for Grok. Scope it to your account. Provider API keys are never forwarded by the Cloudflare provider.
4. Save and select **Transcription > Provider > Cloudflare AI Gateway**. Use **Transcription > Model** to change models later.

The token is stored in Windows Credential Manager. Account ID, Gateway ID, model, and other nonsecret settings are saved in TOML; leaving the dialog's token field blank preserves the saved token.

Grok uses `api.cloudflare.com` and requires a Cloudflare token with **Account > Workers AI > Read** permission plus sufficient AI Gateway credits for third-party inference. It uses only your Cloudflare token, without an xAI key. Each recording is finalized with `audio.done`, then the next recording opens a fresh streaming connection. Streaming model access and forwarding of interim results must be checked with your credentials. See [Cloudflare Grok STT](https://developers.cloudflare.com/ai/models/xai/grok-stt/) and the [unified API authentication requirements](https://developers.cloudflare.com/ai-gateway/usage/rest-api/).

The OpenAI GPT Live Transcribe and GPT Transcribe models are not available on Cloudflare's unified model endpoint and are omitted from the Cloudflare menu. Existing configurations retain their model IDs but give an actionable error; select a supported Cloudflare model or use the direct OpenAI provider. The old `use_byok` setting remains readable for compatibility and no longer forwards provider keys.

The available models are limited to the speech protocols implemented by ParrotInk. Gateway support for an arbitrary model does not make it a compatible transcription model. Gateway's chat Dynamic Routing does not perform live audio model switching; ParrotInk switches connections at phrase boundaries. See the [Cloudflare realtime WebSocket guide](https://developers.cloudflare.com/ai-gateway/usage/websockets-api/realtime-api/) and [Gateway BYOK documentation](https://developers.cloudflare.com/ai-gateway/configuration/bring-your-own-keys/).

---

## User Manual: How it Works

### Simple Use (The "3-Step Flow")
1. **Click** into the application where you want to type (Notion, Slack, Word, etc.).
2. **Press** `Ctrl + Alt + V` (or your custom hotkey).
3. **Speak**. Your words will appear instantly. Stop speaking or press any key to finish.

### Operation Modes
ParrotInk monitors a global hotkey via native Win32 hooks. You can switch between two distinct modes via the tray menu (**Settings > Hold to Talk**):

#### 1. Hold to Talk (The "Walkie-Talkie")
*Best for short bursts, quick replies, and coding snippets.*
- **Action:** Press and **hold** your hotkey.
- **Dictate:** Speak your mind.
- **Stop:** **Release** the hotkey. Audio capture stops when you let go; the pending phrase is finalized before the session closes.

#### 2. Toggle Mode (The "Hands-Free")
*Best for long-form writing, drafting long emails, or deep thinking.*
- **Action:** Press the hotkey **once** to start recording. You can now take your hands off the keyboard and focus entirely on your speech.
- **Stop:** Press the hotkey again to finish.
- **Smart Stop:** If you start typing manually on your keyboard while it's listening, ParrotInk will **automatically stop** the session.

Click-away cancellation observes native mouse events without consuming them. In control scope, Windows UI Automation identifies the focused editor and its bounds when available; applications without accessible editors retain native control matching. Focus checks run off the input-hook thread. Leaving the editor cancels queued transcription so late results cannot enter another field.

Stop-time errors now identify whether the provider failed to finalize or final text could not be inserted. Error logs include the provider, model, stage, elapsed time, and pending insertion count without transcript contents or credentials.

---

## Customization & Advanced Settings

### Changing your Hotkey
1. Right-click the tray icon.
2. Select **Settings > Change Hotkey...**.
3. Press the new key combination (e.g., `Alt + S` or `Ctrl + Space`). ParrotInk saves it instantly.

Use one main key, with optional Ctrl, Alt, Shift, or Windows modifiers. Function keys,
navigation keys, and punctuation keys are supported. Press Escape or click the recorder
to cancel and keep your current shortcut active. Holding a toggle shortcut triggers it
once; release it before pressing again. Forwarded keyboard input, including Mouse
Without Borders, is accepted on the machine running ParrotInk.

<details>
<summary><b>⚙️ Deep Configuration (Advanced Users)</b></summary>

ParrotInk follows a **Portable-First** configuration strategy. It looks for its settings in the following order:

1.  **Portable Mode**: A `config.toml` file located in the same folder as the `ParrotInk.exe`. (Ideal for USB drives or custom installs).
2.  **Standard Mode**: `%APPDATA%\ParrotInk\config.toml` (Used if no local file is found).

**How to modify settings:**
1.  Right-click the tray icon and select **Tools > 1. Open Configuration File**.
2.  Edit the `config.toml` in your preferred text editor (like Notepad).
3.  **Crucial:** After saving your changes, right-click the tray icon and select **Tools > 2. Load Configuration** for the changes to take effect immediately without restarting the app.

**Available Tuning:**
- **HUD Styles**: Customize the Skia-powered HUD appearance.
- **Acoustic Profiles**: Switch between `Headset` (near-field) and `Laptop Mic` (far-field) profiles.
- **Latency Tuning**: Choose between `Fast`, `Balanced`, or `Accurate` profiles to match your speaking pace.

Detailed documentation on all technical settings and their default values can be found in the [config.example.toml](./config.example.toml) file located in the project root.
</details>

---

## Privacy & Security

As an open-source project, transparency is our priority:
- **Encrypted Storage**: Your API keys are stored directly in the **Windows Credential Manager**, encrypted at the OS level.
- **No Local Audio Storage**: Audio is streamed via encrypted WebSockets to the provider and is **never** saved to your hard drive.
- **Local Logs & Stats**: Application logs and statistics are stored locally. Cloudflare Gateway logging and retention depend on your gateway settings; configure them in the Cloudflare dashboard.

### Understanding the Icon
ParrotInk stays out of your way in the **System Tray**. The icon color tells you exactly what the app is doing:
- **Grey**: **Idle** — App is ready and waiting for your hotkey.
- **Blue**: **Listening** — Capturing your voice and streaming text.
- **Yellow**: **Connecting** — Establishing a secure link to the AI.
- **Red**: **Error** — Something is wrong (usually a missing API key).

---

## Building from Source

ParrotInk is built with Python 3.11+ and uses modern, high-performance libraries like `skia-python` for rendering and `sounddevice` for low-latency audio capture.

1.  **Prerequisites**:
    - Python 3.11+
    - [uv](https://github.com/astral-sh/uv) (for dependency management)
2.  **Clone & Setup**:
    ```powershell
    git clone https://github.com/Aalwattar/ParrotInk.git
    cd ParrotInk
    uv sync
    ```
3.  **Run Locally**:
    ```powershell
    uv run main.py
    ```

---

## Contributing & Community

ParrotInk is actively maintained and welcomes contributions!
- **Found a bug?** Open an issue on the [GitHub Issue Tracker](https://github.com/Aalwattar/ParrotInk/issues).
- **Code Style:** We use `ruff` for linting and formatting, and `mypy` for strict type checking.

---

## License

Distributed under the **MIT License**. See `LICENSE` for more information.
Built for speed. Built for Windows. Built for you.
