<p align="center">
  <img src="assets/icons/icon_128.png" width="128" alt="ParrotInk Logo">
</p>

# 🦜 ParrotInk: Stop Typing. Start Thinking.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Latest Release](https://img.shields.io/github/v/release/Aalwattar/ParrotInk?sort=semver)](https://github.com/Aalwattar/ParrotInk/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)](https://www.microsoft.com/windows)

### High-accuracy, ultra-low latency real-time voice-to-text — Native for Windows.

You think faster than you type. **ParrotInk** closes that gap. It is the only open-source, Windows-native application that brings professional-grade, real-time voice-to-text directly to your cursor. With a **polished visual identity** and high-fidelity tray feedback, ParrotInk streams your words instantly so you never lose your flow state.

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
- **Automatic Background Updates:** Downloads new versions silently in the background using Windows BITS, with one-click installation.
- **Smart Injection:** Automatically stops recording if you start typing manually, **preventing frustrating text collisions.**
- **Secure by Design:** API keys are stored safely in the Windows Credential Manager, **protecting your sensitive credentials.**

---

## 🖼️ Visual Preview

### Real-time English & RTL (Arabic) Support
ParrotInk natively handles mixed-language environments and Right-to-Left (RTL) text.

https://github.com/Aalwattar/ParrotInk/raw/master/assets/parriotink2.mp4

*(Note: Demonstration showing the real-time streaming, Skia-powered HUD with Acrylic blur, and RTL alignment.)*

---

## 📥 Download & Install

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

## 🚀 Getting Started

1.  **Launch**: Open `ParrotInk-Setup.exe` (or `ParrotInk.exe`).
2.  **Windows Security**:
    > Because ParrotInk is a new open-source project and is not yet signed with a paid Microsoft Developer certificate, you may see a "Windows protected your PC" warning.
    >
    > To run the app: Click **More info** -> **Run anyway**.
3.  **Setup API Key**:
    *   **What is an API Key?** A "secret password" that allows ParrotInk to securely talk to the AI models (OpenAI or AssemblyAI).
    *   **How to get one**: Sign up for a free account at [AssemblyAI](https://www.assemblyai.com/dashboard/) or [OpenAI](https://platform.openai.com/api-keys).
    *   **Where to put it**: Right-click the ParrotInk tray icon and select **Settings > API Credentials**.
4.  **Start Dictating**: Press `Ctrl + Alt + V` (default) and start speaking. Your words will appear instantly at your cursor!

---

## 💎 Choose Your Engine

ParrotInk requires you to bring your own API key. You only pay the AI providers for the raw milliseconds of audio they process.

### 🏆 AssemblyAI (Best for Professional English & Speed)
**Featuring Universal-3 Pro (`u3-rt-pro`) and Instructional Prompting.**
- **Why we recommend it:** The latest **U3 Pro** model is the industry benchmark for streaming accuracy. It supports **Instructional Prompting**, allowing you to guide the AI (e.g., "Always use medical terminology" or "Format as a list").
- **Get Started for $0:** New users currently receive **$50 in free credit** upon signing up.
- **Advanced Features:** Supports **Shaded Partials** in the HUD, letting you see the AI "thinking" in real-time before finalizing the text.
- **Setup:** Paste your key from the [AssemblyAI Dashboard](https://www.assemblyai.com/dashboard/) into the ParrotInk menu.

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
- **Local Logs & Stats**: All diagnostic data is kept strictly on your machine:
  - **Logs**: `%LOCALAPPDATA%\ParrotInk\Logs\parrotink.log` (Rotational, capped at 30MB).
  - **Statistics**: `%APPDATA%\ParrotInk\Stats\stats.json`.

### 🎨 Visual Feedback: Understanding the Icon
ParrotInk stays out of your way in the **System Tray** (the icons next to your clock). The icon color tells you exactly what the app is doing:
- **🔘 Grey**: **Idle** — App is ready and waiting for your hotkey.
- **🔵 Blue**: **Listening** — Capturing your voice and streaming text.
- **🟡 Yellow**: **Connecting** — Establishing a secure link to the AI.
- **🔴 Red**: **Error** — Something is wrong (usually a missing API key).

---

## 🔍 User Manual: How it Works

### ⚡ Simple Use (The "3-Step Flow")
1. **Click** into the application where you want to type (Notion, Slack, Word, etc.).
2. **Press** `Ctrl + Alt + V` (or your custom hotkey).
3. **Speak**. Your words will appear instantly. Stop speaking or press any key to finish.

### 🎮 Operation Modes
ParrotInk monitors a global hotkey via native Win32 hooks. You can switch between two distinct modes via the tray menu (**Settings > Hold to Talk**):

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
