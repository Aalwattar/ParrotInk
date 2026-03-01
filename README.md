# 🎙️ ParrotInk: Stop Typing. Start Thinking.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/github/v/release/Aalwattar/ParrotInk)](https://github.com/Aalwattar/ParrotInk/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)](https://www.microsoft.com/windows)

### Experience ultra-low latency, high-accuracy real-time voice-to-text — Native for Windows.

**ParrotInk** is a high-performance system tray application that lets you type with your voice into **any** Windows application. Whether you are coding in VS Code, writing emails in Outlook, or chatting in Slack, ParrotInk streams your words **instantly** to your cursor.

---

## 📖 Table of Contents
- [🚀 The Real-Time Advantage](#-the-real-time-advantage)
- [✨ Key Features](#-key-features)
- [📥 Download & Install](#-download--install)
- [💎 Choose Your Engine](#-choose-your-engine)
- [🔍 User Manual: How it Works](#-user-manual-how-it-works)
- [🛠️ Customization & Advanced Settings](#-customization--advanced-settings)
- [🏗️ Building from Source](#-building-from-source)
- [🛡️ Privacy & Security](#-privacy--security)
- [⚖️ License](#-license)

---

## 🚀 The Real-Time Advantage
I built ParrotInk because existing tools often felt slow. Most use "batch processing"—you speak, wait several seconds, and then a block of text finally dumps onto the screen. It breaks your concentration and ruins your creative flow.

**ParrotInk is built for speed.** It uses advanced streaming ASR models to type **as you say the words**. No waiting. No blocks of text. Just natural, fluid creation at 150+ words per minute. 

### Key Features
- **Zero-Latency Feel:** Real-time streaming ensures your text appears as you speak.
- **Global Language Support:** Works with almost any language (English, Spanish, French, Chinese, Japanese, etc.) via world-class AI models.
- **Native RTL Support:** Full support for **Arabic**, Hebrew, and other Right-to-Left languages with correct character shaping and HUD alignment.
- **Smart Injection:** Automatically stops recording if you start typing manually to prevent collisions.
- **Secure:** API keys are stored in the Windows Credential Manager.

---

## 🖼️ Visual Preview

### Real-time English & RTL (Arabic) Support
ParrotInk handles mixed-language environments and Right-to-Left (RTL) text natively.

| English Dictation | Arabic (RTL) Dictation |
| :--- | :--- |
| ![English HUD Example](https://raw.githubusercontent.com/Aalwattar/ParrotInk/master/arabic_test.png) | ![Arabic HUD Example](https://raw.githubusercontent.com/Aalwattar/ParrotInk/master/hud_rtl_verification.png) |

*(Note: Screenshots show the Skia-powered HUD with Acrylic blur and RTL alignment.)*

---

## 📥 Download & Install

ParrotInk is a **portable** application. There is no installer needed; just download the EXE and run it.

1.  **Download**: Click the button below to get the latest version.
    [![Download ParrotInk](https://img.shields.io/badge/Download-ParrotInk.exe-brightgreen?style=for-the-badge&logo=windows)](https://github.com/Aalwattar/ParrotInk/releases/latest/download/ParrotInk.exe)
2.  **Launch**: Open `ParrotInk.exe`. You will see a new 🎙️ icon in your system tray (bottom right).
3.  **Setup API Key**: Right-click the tray icon and select **Settings > Setup API Keys**.
4.  **Go**: Press `Ctrl + Alt + V` (default) and start speaking.

> **Pro Tip:** To have ParrotInk start automatically with your computer, right-click the tray icon and check **Settings > Run at Startup**.

---

## 💎 Choose Your Engine

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

## 🔍 User Manual: How it Works

ParrotInk lives in your system tray and monitors a global hotkey. You can switch between two distinct modes via the tray menu (**Settings > Hold to Talk**):

### 1. Hold to Talk (The "Walkie-Talkie")
*Best for short bursts, quick replies, and coding snippets.*
- **Action:** Press and **hold** your hotkey.
- **Dictate:** Speak your mind.
- **Stop:** **Release** the hotkey. The session ends immediately when you let go.

### 2. Toggle Mode (The "Hands-Free")
*Best for long-form writing, drafting long emails, or deep thinking.*
- **Action:** Press the hotkey **once** to start recording. You can now take your hands off the keyboard and focus entirely on your speech.
- **Stop:** Press the hotkey again to finish.
- **Smart Stop:** If you start typing manually on your keyboard while it's listening, ParrotInk will **automatically stop** the session to prevent your voice and your typing from colliding.

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
- **Latency Tuning**: Choose between `Fast`, `Balanced`, or `Accurate` profiles.

Detailed documentation on all settings can be found in the [config.example.toml](./config.example.toml) file.

---

## 🏗️ Building from Source

If you want to contribute or build the EXE yourself:

1.  **Prerequisites**:
    - Python 3.12+
    - [uv](https://github.com/astral-sh/uv) (for dependency management)
2.  **Clone & Setup**:
    ```powershell
    git clone https://github.com/Aalwattar/ParrotInk.git
    cd ParrotInk
    uv sync
    ```
3.  **Run**:
    ```powershell
    uv run main.py
    ```
4.  **Build EXE**:
    ```powershell
    .\scripts\build_onefile.ps1
    ```

---

## 💰 What does it cost?
ParrotInk is open-source and free. You only pay the AI providers for the raw milliseconds of audio they process.

- **Casual User**: A few quick Slack replies a day? Roughly **$0.50/month**.
- **Power User**: 2 hours of dictation every day? Roughly **$5.00 - $7.00/month**.

---

## 🛡️ Privacy & Security

- **Encrypted Storage**: Your API keys are stored in the **Windows Credential Manager**, encrypted at the OS level.
- **No Local Audio Storage**: Audio is streamed via encrypted WebSockets and is never saved to your hard drive.
- **Lightweight**: Log files are rotational and capped at **30MB** total.

---

## ⚖️ License

Distributed under the **MIT License**. See `LICENSE` for more information.
Built for speed. Built for Windows. Built for you.
