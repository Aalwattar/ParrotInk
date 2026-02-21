# 🎙️ Stop Typing. Start Thinking. 
### Professional, Real-Time Voice-to-Text — Native for Windows.

**ParrotInk** is a high-performance system tray application that lets you type with your voice into **any** Windows application. Whether you are coding in VS Code, writing emails in Outlook, or chatting in Slack, ParrotInk streams your words **instantly** to your cursor.

---

## 🚀 The Real-Time Advantage
I built ParrotInk because existing open-source tools were frustrating. Most use "batch processing"—you speak, wait several seconds (sometimes up to a **full minute**), and then a block of text dumps onto the screen. It’s clunky, breaks your flow, and feels like the past.

**ParrotInk is the future:** It streams your words **as you say them**. No waiting. No blocks of text. Just natural, fluid creation at 150+ words per minute.

---

## ⚡ The 3-Step "Quick-Start" Plan

1. **Download & Run**: Grab the [latest release](https://github.com/Aalwattar/ParrotInk/releases) and launch `ParrotInk.exe`.
2. **Connect your Brain**: Right-click the tray icon and select **Settings > Setup API Keys**.
3. **Speak Naturally**: Press `Ctrl + Alt + V` and watch your words appear in real-time.

---

## 💎 Choose Your Engine

### 🏆 AssemblyAI (Recommended)
**Superior Accuracy for English & $50 Free Credit.**
- **Best For:** Users who want the highest possible accuracy in English and a generous starting point.
- **Get Started for Free:** New users currently receive **$50 in free credit**. You can start dictating immediately without paying a penny.
- **Language Support:** Incredible performance for English. Robust and growing support for major languages like Spanish, French, and German.

### 🟢 OpenAI (The Global Standard)
**The Multilingual Powerhouse.**
- **Best For:** Users who need to dictate in a wide variety of global languages.
- **Language Support:** Supports **50+ languages** natively (Japanese, Chinese, Arabic, Portuguese, etc.).
- **Setup:** Note that OpenAI requires a small pre-paid balance (e.g., $5) to activate their Realtime API.

---

## 🔍 User Manual: How to Dictate

ParrotInk adapts to the way you work. You can switch between two distinct modes via the tray menu (**Settings > Hold to Talk**):

### 1. Hold to Talk (The "Walkie-Talkie")
*Perfect for short bursts, messages, and quick commands.*
- **How it works:** Press and **hold** your hotkey. Speak. **Release** the key when you are finished.
- **Result:** The dictation stops the moment you let go.

### 2. Toggle Mode (The "Hands-Free")
*Perfect for long-form writing, emails, and coding sessions.*
- **How it works:** Press the hotkey **once** to start recording. You can now take your hands off the keyboard.
- **How to stop:** Press the hotkey again, **OR press ANY other key** on your keyboard. ParrotInk detects your manual input and gracefully ends the session.

### ⌨️ Customizing your Hotkey
Don't like `Ctrl + Alt + V`? No problem.
1. Right-click the tray icon.
2. Select **Settings > Change Hotkey...**.
3. A window will appear—simply press the new key combination you want to use. ParrotInk will save it instantly.

---

## 💰 What does it cost?
ParrotInk is open-source and free. You only pay the AI providers for what you use.

**Real-world Example:**
- **Casual User:** A few emails a day? Spend **less than $0.50 a month**.
- **Power User:** 2 hours of dictation every day? Roughly **$5.00 to $7.00 a month**.
- **The Verdict:** It’s cheaper than one cup of coffee to gain dozens of hours of your life back.

---

## ❓ FAQ

**Q: Does it work on Mac or Linux?**
No. ParrotInk is built specifically for **Windows 10 and 11** to leverage native Win32 hooks and the Windows Credential Manager for maximum performance and security.

**Q: Can I use it offline?**
No. ParrotInk uses world-class AI models that require a secure internet connection to stream your audio to the providers and get text back in real-time.

**Q: Is my voice recorded?**
We never save your audio to your hard drive. Your voice is streamed via encrypted WebSockets directly to your chosen provider (OpenAI or AssemblyAI) and then discarded.

**Q: Where is the configuration file?**
Your settings are stored in `%APPDATA%\ParrotInk\config.toml`. You can open it directly from the tray menu under **Settings > Open Configuration File**.

---

## 🛡️ Reliability & Logging
- **Space-Efficient:** Technical logs are stored in `%LOCALAPPDATA%\ParrotInk\`. Our rotational system **never exceeds 30MB**.
- **Security:** API keys are stored in the **Windows Credential Manager** (encrypted at the OS level).
- **HUD:** A beautiful, Skia-powered Acrylic HUD provides real-time visual feedback of your transcription.

**MIT License.** Built for speed. Built for Windows. Built for you.
