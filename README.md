# ✨ ParrotInk: Professional Real-Time Voice-to-Text for Windows

**ParrotInk** is a powerful, low-latency system tray application that lets you type with your voice into **any** Windows application. Whether you are coding in VS Code, writing emails in Outlook, or chatting in Slack, ParrotInk injects your words instantly where your cursor is.

---

## 🚀 Why ParrotInk?

- **Type Anywhere:** Works globally across Windows. Just press a hotkey and start talking.
- **Pro-Grade Accuracy:** Powered by the latest **OpenAI Realtime** and **AssemblyAI Streaming V3** models.
- **Privacy First:** Your API keys are stored in the encrypted **Windows Credential Manager**, never in plain text.
- **Distraction-Free:** Runs quietly in your system tray. A beautiful, acrylic HUD (Heads-Up Display) shows your words in real-time.
- **Smart Interaction:** Automatically stops listening if you start typing manually—no more text collisions.

---

## 🛠️ Quick Start (Get up and running in 2 minutes)

### 1. Installation
Download the latest [ParrotInk.exe](https://github.com/Aalwattar/ParrotInk/releases) or run from source:
```powershell
uv sync
uv run python main.py
```

### 2. Connect Your Voice (API Keys)
Right-click the **ParrotInk** icon in your system tray and select **Settings > Setup API Keys**.

#### **Option A: OpenAI (Fastest)**
1. Go to the [OpenAI Dashboard](https://platform.openai.com/api-keys).
2. Create a new Secret Key.
3. Paste it into ParrotInk under **Set OpenAI Key...**.

#### **Option B: AssemblyAI (Accurate)**
1. Go to the [AssemblyAI Dashboard](https://www.assemblyai.com/dashboard/).
2. Copy your **API Key** from the sidebar.
3. Paste it into ParrotInk under **Set AssemblyAI Key...**.

---

## ⌨️ Global Controls

- **Default Hotkey:** `Ctrl + Alt + V` (Customizable in settings)
- **Hold to Talk:** (Default) Press and hold to dictate; release to stop.
- **Toggle Mode:** Click once to start recording; click any key to stop.

### 🎨 Visual Feedback (Tray Icon)
The icon color tells you exactly what ParrotInk is doing:
- 🔵 **Blue:** **Listening.** Your voice is being transcribed.
- 🟡 **Yellow:** **Connecting.** Handshaking with the provider.
- 🔴 **Red:** **Error.** Check your internet or API key.
- ⚪ **Grey:** **Idle.** Ready and waiting for your command.

---

## ⚙️ Advanced Customization

ParrotInk is highly configurable via `%APPDATA%\ParrotInk\config.toml`. 

- **Custom Hotkeys:** Use `win`, `ctrl`, `alt`, `shift` combinations.
- **Acoustic Profiles:** Optimized settings for **Headsets** vs. **Laptop Microphones**.
- **Latency Profiles:** Choose between `Fast` (speed) or `Accurate` (better pauses).
- **Sound Feedback:** Enable or disable the "Start/Stop" beeps.

---

## 🛡️ Security & Privacy

ParrotInk is designed for professionals who value their data:
- **Zero Local Storage:** We never save your audio or transcripts to disk.
- **Encrypted Secrets:** We use the `keyring` library to leverage Windows' native security for your API keys.
- **Open Source:** Auditable code that puts you in control.

---

## 📝 License
MIT License. Created with ❤️ for productive humans.
