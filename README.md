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

## 💎 Choose Your Engine (Provider Setup)

### 🏆 AssemblyAI (Recommended)
**Faster. More Accurate. Better Value.**
AssemblyAI’s Streaming V3 is our top recommendation for the best ParrotInk experience.
- **Get Started for Free:** Currently, AssemblyAI offers **$50 in free credit** to new users. You can start dictating immediately without spending a penny. *(Note: Check their dashboard for current terms).*
- **Setup:** Copy your API Key from the [AssemblyAI Dashboard](https://www.assemblyai.com/dashboard/) and paste it into the ParrotInk tray menu.
- **Languages:** Best-in-class English accuracy, with robust support for Spanish, French, German, and more.

### 🟢 OpenAI (The Global Standard)
*Versatile and supports 50+ languages natively.*
- **Setup:** Get a key from the [OpenAI Platform](https://platform.openai.com/api-keys). Note that OpenAI requires a small pre-paid balance (e.g., $5) to activate the Realtime API.
- **Languages:** Massive global support (Japanese, Chinese, Arabic, etc.).

---

## 💰 What does it cost?
ParrotInk is open-source and free. You only pay the AI providers for the raw processing time you use.

**Real-world Example:**
- **The Casual User:** A few quick emails and Slack replies? You’ll likely spend **less than $0.50 a month**.
- **The Power User:** Dictating 2 hours of deep-work every day? Your monthly bill will be roughly **$5.00 to $7.00**.
- **The Verdict:** It’s cheaper than one cup of coffee to gain dozens of hours of your life back.

---

## 🔍 The Deep Dive (User Manual)

### 🎛️ Tray Icon Controls
The tray icon is your command center. Right-click it to:
- **Switch Providers:** Instantly toggle between OpenAI and AssemblyAI.
- **Toggle "Hold to Talk":** Choose between holding the key while speaking or a simple "click-to-start / click-to-stop" mode.
- **Audio Feedback:** Enable/Disable the start/stop beeps.
- **HUD Settings:** Show or hide the real-time transcription overlay (the Acrylic HUD).
- **Statistics:** View your daily, monthly, and lifetime dictation stats (word counts and time saved).

### 📝 Advanced Configuration (`config.toml`)
For total control, select **Settings > Open Configuration File**. 
- **Storage Location:** Your settings are stored safely in `%APPDATA%\ParrotInk\config.toml`.
- **Manual Tuning:** In this file, you can change your global hotkey, adjust microphone sensitivity (VAD), and set "Acoustic Profiles" (optimizing for a **Headset** vs. a **Laptop Mic**).
- **Self-Documenting:** The config file contains detailed comments explaining every single setting.

### 🛡️ Reliability & Logging
ParrotInk is built for "always-on" reliability:
- **Rotational Logs:** Technical logs are stored in `%LOCALAPPDATA%\ParrotInk\`. We use a smart rotation system that **never exceeds 30MB**, so it will never bloat your hard drive.
- **Security:** API keys are stored in the **Windows Credential Manager** (encrypted at the OS level).
- **Auto-Update:** If you modify your `config.toml`, ParrotInk detects the change and reloads your settings instantly—no restart required.

---

## 🎨 Icon Status Guide
- ⚪ **Grey:** Idle. Ready and waiting.
- 🟡 **Yellow:** Connecting. Handshaking with the AI servers.
- 🔵 **Blue:** **Listening.** Everything you say is being typed.
- 🔴 **Red:** Error. (Usually a missing API key or no internet).

---

## 🤝 Contributing & Support
ParrotInk is a community project. If you're a developer or a user with feedback, check out our `architecture.md` or open an issue.

**MIT License.** Built for speed. Built for Windows. Built for you.
