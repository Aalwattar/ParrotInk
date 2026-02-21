# 🎙️ Stop Typing. Start Thinking. 
### The world’s fastest, real-time open-source voice-to-text for Windows.

**ParrotInk** isn't just another dictation tool—it’s a productivity superpower. While most voice-to-text apps make you wait seconds for a "batch" of text to appear, ParrotInk streams your words **instantly** into any application, exactly where your cursor is. 

Unleash your thoughts at 150+ words per minute and eliminate the friction of the keyboard.

---

## ⚡ The 3-Step "Quick-Start" Plan

1. **Download & Run**: Grab the [latest release](https://github.com/Aalwattar/ParrotInk/releases) and launch `ParrotInk.exe`.
2. **Connect your Brain**: Right-click the tray icon and select **Settings > Setup API Keys**.
3. **Speak Naturally**: Press `Ctrl + Alt + V` and watch your words appear in real-time.

---

## 💎 Why ParrotInk is Different

I built ParrotInk because I was frustrated. Existing tools were either expensive, closed-source, or used "batch processing"—where you speak, wait 3 seconds, and then a block of text dumps onto the screen. It felt clunky and broken.

**ParrotInk is the solution:**
- **Zero-Latency Streaming:** Powered by the most advanced ASR (Automatic Speech Recognition) models on Earth. You see your text as you say it.
- **Works Everywhere:** From VS Code and Slack to Excel and Outlook. If you can type in it, you can speak in it.
- **Professional Grade:** Uses the same tech that powers world-class AI agents, optimized for your desktop.

---

## 🛠️ Choose Your Engine (Provider Setup)

ParrotInk gives you access to the "Big Two" of AI transcription. Setup is easy and takes less than 60 seconds.

### 🟢 OpenAI (The Global Standard)
*Fast, versatile, and supports almost every major language.*
1. **Get your Key:** Log in to [OpenAI API Keys](https://platform.openai.com/api-keys).
2. **Create Key:** Click **"+ Create new secret key"**, name it "ParrotInk", and copy it.
3. **Paste:** Enter it into the ParrotInk tray menu.
4. **Languages:** Supports 50+ languages (English, Spanish, French, German, Japanese, Chinese, etc.).

### 🟣 AssemblyAI (The Accuracy Leader)
*Incredible accuracy and the industry-leading V3 Streaming API.*
1. **Get your Key:** Copy your API Key from the [AssemblyAI Dashboard](https://www.assemblyai.com/dashboard/).
2. **Paste:** Enter it into the ParrotInk tray menu.
3. **Languages:** Optimized for English, with expanding support for Spanish, French, German, and more.

---

## 💰 What does it cost?
ParrotInk is open-source and free, but the AI models you use cost a tiny fraction of a cent per minute. 

**Real-world Example:**
- **The Casual User:** A few quick emails and Slack replies a day? You’ll likely spend **less than $0.50 a month**.
- **The Heavy User:** Dictating 2 hours of deep-work brainstorming every single day? Your monthly bill will be roughly **$5.00 to $7.00**.
- **Comparison:** It’s cheaper than a single cup of coffee to gain hours of your life back.

---

## 🎨 Icon Status Guide
Stay in control with simple visual feedback in your tray:
- ⚪ **Grey:** Idle. ParrotInk is ready and waiting.
- 🟡 **Yellow:** Connecting. Handshaking with the AI servers.
- 🔵 **Blue:** **Listening.** Everything you say is being typed.
- 🔴 **Red:** Error. (Usually a missing API key or no internet).

---

## 🛡️ Technical Details & Security
For the developers and the privacy-conscious:
- **Security:** Keys are stored in the **Windows Credential Manager** (encrypted at the OS level). We never see your keys.
- **Privacy:** Audio is streamed via secure WebSockets and is never stored locally.
- **HUD:** High-performance **Skia-based Acrylic HUD** for real-time visual confirmation.
- **Stack:** Python 3.11+, `uv` for lightning-fast dependency management, and native Win32 hooks for global interaction.

---

## 🤝 Contributing
ParrotInk is a community project. If you're a developer who wants to help build the future of human-computer interaction, check out our `architecture.md`.

**MIT License.** Built for speed. Built for you.
