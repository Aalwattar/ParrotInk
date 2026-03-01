# 🎙️ ParrotInk: Stop Typing. Start Thinking.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Latest Tag](https://img.shields.io/github/v/tag/Aalwattar/ParrotInk?label=latest)](https://github.com/Aalwattar/ParrotInk/tags)
[![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)](https://www.microsoft.com/windows)

### High-accuracy, ultra-low latency real-time voice-to-text — Native for Windows.

You think faster than you type. **ParrotInk** closes that gap. It is the only open-source, Windows-native application that brings professional-grade, real-time voice-to-text directly to your cursor. Whether you are coding in VS Code, drafting emails in Outlook, or brainstorming in Notion, ParrotInk streams your words instantly so you never lose your flow state.

---

## 📖 Table of Contents
- [🚀 The Story Behind ParrotInk](#-the-story-behind-parrotink)
- [✨ Key Features](#-key-features)
- [🖼️ Visual Preview](#-visual-preview)
- [📥 Download & Install](#-download--install)
- [💎 Choose Your Engine](#-choose-your-engine)
- [💰 What does it cost?](#-what-does-it-cost)
- [🛡️ Privacy & Security](#-privacy--security)
- [🔍 User Manual: How it Works](#-user-manual-how-it-works)
- [🛠️ Customization & Advanced Settings](#-customization--advanced-settings)
- [🏗️ Building from Source](#-building-from-source)
- [🤝 Contributing & Community](#-contributing--community)
- [⚖️ License](#-license)

---

## 🚀 The Story Behind ParrotInk

I built ParrotInk because existing dictation tools broke my concentration. They either forced me to wait for "batch processing" to dump a giant block of text onto the screen, or—like the built-in Windows dictation (`Win + H`)—struggled heavily with slight accents. 

I wanted true real-time streaming with professional-grade accuracy, and I wanted the freedom to use my own API keys from industry leaders like OpenAI and AssemblyAI. When I couldn't find a single open-source, Windows-native tool that met these standards, I decided to build it. ParrotInk is the result: a tool designed for people who want to type as fast as they can think, without the wait.

---

## ✨ Key Features

- **Zero-Latency Feel:** Real-time streaming ensures your text appears as you speak, **keeping you in the zone.**
- **Global Language Support:** Works with almost any language (English, Spanish, French, Chinese, Japanese, etc.) via world-class AI models, **so you can work in your native tongue.**
- **Native RTL Support:** Full support for **Arabic** and other Right-to-Left languages with correct character shaping and HUD alignment.
- **Smart Injection:** Automatically stops recording if you start typing manually, **preventing frustrating text collisions.**
- **Secure by Design:** API keys are stored safely in the Windows Credential Manager, **protecting your sensitive credentials.**

---

## 🖼️ Visual Preview

### Real-time English & RTL (Arabic) Support
ParrotInk natively handles mixed-language environments and Right-to-Left (RTL) text.

![HUD Examples](./hud_rtl_verification.png)

*(Note: Screenshots show the Skia-powered HUD with Acrylic blur and RTL alignment.)*

---

## 📥 Download & Install

ParrotInk is a **portable** application. There is no installer needed; just download the EXE and run it.

1.  **Download**: Click the button below to get the latest version.
    [![Download ParrotInk](https://img.shields.io/badge/Download-ParrotInk.exe-brightgreen?style=for-the-badge&logo=windows)](https://github.com/Aalwattar/ParrotInk/releases/latest/download/ParrotInk.exe)
2.  **Launch**: Open `ParrotInk.exe`. You will see a new 🎙️ icon in your system tray (bottom right).
3.  **Setup API Key**: Right-click the tray icon and select **Settings > Setup API Keys**.
4.  **Start Dictating**: Press `Ctrl + Alt + V` (default) and start speaking.

> **Pro Tip:** To have ParrotInk start automatically with your computer, right-click the tray icon and check **Settings > Run at Startup**.

---

## 💎 Choose Your Engine

ParrotInk requires you to bring your own API key. You only pay the AI providers for the raw milliseconds of audio they process.

### 🏆 AssemblyAI (Best for English & European Languages)
**Optimized for professional use and low-latency response.**
- **Why we recommend it:** If you are dictating in **English, Spanish, French, or German**, AssemblyAI’s Streaming V3 is arguably the most accurate and responsive real-time model available today.
- **Get Started for $0:** New users currently receive **$50 in free credit** upon signing up. You can start dictating immediately without paying a single penny.
- **Setup:** Copy your API Key from the [AssemblyAI Dashboard](https://www.assemblyai.com/dashboard/) and paste it into the ParrotInk tray menu.

### 🟢 OpenAI (The Global & RTL Powerhouse)
**Unmatched support for 50+ languages and Arabic.**
- **Why use it:** For native **Arabic**, Japanese, Chinese, or multilingual workflows, OpenAI provides world-class coverage.
- **Language Support:** Perfect for users who switch between global languages frequently.
- **Setup:** Requires a key from the [OpenAI Platform](https://platform.openai.com/api-keys). Note: OpenAI requires a small pre-paid balance (usually $5 minimum) to activate their Realtime API.

---

## 💰 What does it cost?
ParrotInk is open-source and **100% free software**. Your only cost is your direct usage with the API providers (OpenAI or AssemblyAI), meaning there is no middleman markup.

- **Casual User**: A few quick Slack replies a day? Roughly **$0.50/month**.
- **Power User**: 2 hours of dictation every day? Roughly **$5.00 - $7.00/month**.

---

## 🛡️ Privacy & Security

As an open-source project, transparency is our priority:
- **Encrypted Storage**: Your API keys are stored directly in the **Windows Credential Manager**, encrypted at the OS level.
- **No Local Audio Storage**: Audio is streamed via encrypted WebSockets to the provider and is **never** saved to your hard drive.
- **Lightweight Telemetry**: Log files are purely local, rotational, and capped at **30MB** total to prevent drive bloat.

---

## 🔍 User Manual: How it Works

ParrotInk lives in your system tray and monitors a global hotkey via native Win32 hooks. You can switch between two distinct modes via the tray menu (**Settings > Hold to Talk**):

### 1. Hold to Talk (The "Walkie-Talkie")
*Best for short bursts, quick replies, and coding snippets.*
- **Action:** Press and **hold** your hotkey.
- **Dictate:** Speak your mind.
- **Stop:** **Release** the hotkey. The session ends immediately when you let go.

### 2. Toggle Mode (The "Hands-Free")
*Best for long-form writing, drafting long emails, or deep thinking.*
- **Action:** Press the hotkey **once** to start recording. You can now take your hands off the keyboard and focus entirely on your speech.
- **Stop:** Press the hotkey again to finish.
- **Smart Stop:** If you start typing manually on your keyboard while it's listening, ParrotInk will **automatically stop** the session.

---

## 🛠️ Customization & Advanced Settings

### ⌨️ Changing your Hotkey
1. Right-click the tray icon.
2. Select **Settings > Change Hotkey...**.
3. Press the new key combination (e.g., `Alt + S` or `Ctrl + Space`). ParrotInk saves it instantly.

### ⚙️ Deep Configuration
ParrotInk stores its configuration in `%APPDATA%\ParrotInk\config.toml`. 
- **HUD Styles**: Customize the Skia-powered HUD appearance.
- **Acoustic Profiles**: Switch between `Headset` (near-field) and `Laptop Mic` (far-field) profiles.
- **Latency Tuning**: Choose between `Fast`, `Balanced`, or `Accurate` profiles to match your speaking pace.

Detailed documentation on all technical settings can be found in the [config.example.toml](./config.example.toml) file.

---

## 🏗️ Building from Source

ParrotInk is built with Python 3.12+ and uses modern, high-performance libraries like `skia-python` for rendering and `sounddevice` for low-latency audio capture.

1.  **Prerequisites**:
    - Python 3.12+
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
4.  **Build Frozen EXE** (Using PyInstaller):
    ```powershell
    .\scripts\build_onefile.ps1
    ```

---

## 🤝 Contributing & Community

ParrotInk is actively maintained and welcomes contributions!
- **Found a bug?** Open an issue on the [GitHub Issue Tracker](https://github.com/Aalwattar/ParrotInk/issues).
- **Have an idea?** Submit a feature request or open a Pull Request.
- **Code Style:** We use `ruff` for linting and formatting, and `mypy` for strict type checking. See the local CI scripts for our "Definition of Done".

---

## ⚖️ License

Distributed under the **MIT License**. See `LICENSE` for more information.
Built for speed. Built for Windows. Built for you.
