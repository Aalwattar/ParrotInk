# 🎙️ Stop Typing. Start Thinking. 
### The world’s fastest, most accurate real-time voice-to-text — Native for Windows.

**ParrotInk** is a high-performance system tray application that lets you type with your voice into **any** Windows application. Whether you are coding in VS Code, writing emails in Outlook, or chatting in Slack, ParrotInk streams your words **instantly** to your cursor.

---

## 🚀 The Real-Time Advantage
I built ParrotInk because existing open-source tools were incredibly frustrating. Most use "batch processing"—you speak, wait several seconds (and sometimes up to a **full minute**), and then a giant block of text finally dumps onto the screen. It breaks your concentration, ruins your flow, and feels clunky.

**ParrotInk is different.** It uses the most advanced streaming ASR models on the planet to type **as you say the words**. No waiting. No blocks of text. Just natural, fluid creation at 150+ words per minute. It is the closest thing to telepathy for your computer.

---

## ⚡ The 3-Step "Quick-Start" Plan

1. **Download & Run**: Grab the [latest release](https://github.com/Aalwattar/ParrotInk/releases) and launch `ParrotInk.exe`.
2. **Connect your Brain**: Right-click the tray icon and select **Settings > Setup API Keys**.
3. **Speak Naturally**: Press `Ctrl + Alt + V` (default) and watch your words appear in real-time.

---

## 💎 Choose Your Engine

### 🏆 AssemblyAI (Recommended)
**The leader in Accuracy and Speed for English.**
- **Why we recommend it:** AssemblyAI’s Streaming V3 is arguably the most accurate real-time model available today. It is optimized for low-latency and professional use.
- **Get Started for $0:** New users currently receive **$50 in free credit** upon signing up. You can start dictating immediately without paying a single penny. 
- **Setup:** Copy your API Key from the [AssemblyAI Dashboard](https://www.assemblyai.com/dashboard/) and paste it into the ParrotInk tray menu.
- **Language Support:** Optimized for English. Also supports major languages like Spanish, French, and German.

### 🟢 OpenAI (The Multilingual Powerhouse)
**Unmatched support for global languages.**
- **Why use it:** If you need to dictate in something other than English, OpenAI is your best bet. 
- **Language Support:** Supports **50+ languages** natively (Japanese, Chinese, Arabic, Portuguese, French, etc.).
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

### ⌨️ Customizing your Hotkey
You aren't stuck with the defaults. To change your trigger:
1. Right-click the tray icon.
2. Select **Settings > Change Hotkey...**.
3. When the window appears, simply press the new key combination (e.g., `Alt + S` or `Ctrl + Space`). ParrotInk saves it instantly.

---

## 💰 What does it cost?
ParrotInk is open-source and free. You only pay the AI providers for the raw milliseconds of audio they process.

**Real-world Examples:**
- **The Casual User:** A few quick Slack replies and emails a day? You’ll likely spend **less than $0.50 a month**.
- **The Power User:** Dictating 2 hours of deep-work every single day? Your monthly bill will be roughly **$5.00 to $7.00**.
- **The Verdict:** It is cheaper than a single cup of coffee to gain dozens of hours of your life back.

---

## ❓ FAQ

**Q: Does it work on Mac or Linux?**
No. ParrotInk is built specifically for **Windows 10 and 11**. It uses native Win32 hooks for the fastest possible response and the Windows Credential Manager for secure key storage.

**Q: Can I use it offline?**
No. To get the world's most accurate transcription, ParrotInk streams your audio to high-performance AI servers. This requires an active internet connection.

**Q: Is my privacy protected?**
Yes. We never save your audio to your hard drive. It is streamed via encrypted WebSockets directly to the provider (OpenAI or AssemblyAI) and is processed in real-time. API keys are stored in the **Windows Credential Manager**, meaning they are encrypted at the OS level.

**Q: Where are my settings and logs?**
- **Settings:** `%APPDATA%\ParrotInk\config.toml` (accessible via the tray menu).
- **Logs:** `%LOCALAPPDATA%\ParrotInk\`. We use a rotational system that **never exceeds 30MB**, so it won't bloat your drive.

---

## 🛡️ Technical Deep-Dive
- **HUD:** A Skia-powered Acrylic HUD provides real-time visual feedback of your transcription.
- **Acoustic Profiles:** Optimized settings in the config file allow you to switch between **Headset** (near-field) and **Laptop Mic** (far-field) profiles.
- **Latency Tuning:** Choose between `Fast`, `Balanced`, or `Accurate` profiles in the configuration to match your speaking pace.

**MIT License.** Built for speed. Built for Windows. Built for you.
