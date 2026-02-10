# Voice2Text

A real-time voice-to-text system tray application for Windows. It allows you to inject transcribed text directly into any application via simulated typing using a global hotkey.

## Features

- **Real-time Transcription:** Supports OpenAI and AssemblyAI.
- **System Tray Integration:** Discrete background operation with visual status feedback.
- **Secure Credentials:** API keys are stored in the Windows Credential Manager (`keyring`), never in plain text.
- **Smart Toggle:** Use "Hold mode" to listen only while the hotkey is pressed, or "Toggle mode" for a press-to-start/press-to-stop experience.
- **Interaction Safety:** Automatically stops transcription if you start typing manually to prevent text collisions.
- **Dynamic UI:** Menu options are automatically enabled or disabled based on your available API keys.
- **Test Mode:** Built-in mock support for development without consuming API credits.

## Installation

1. Clone the repository.
2. Ensure you have Python 3.10+ installed.
3. Install dependencies:
   ```bash
   uv sync
   ```
   *(Or use `pip install -e .` if not using `uv`)*

## Usage

### Starting the Application

Run the main script to start the tray icon:
```bash
python main.py
```

### CLI Commands

You can use the CLI to manage your API keys securely:

- **Display Help:**
  ```bash
  python main.py --help
  ```

- **Set OpenAI API Key:**
  ```bash
  python main.py set-key openai
  ```

- **Set AssemblyAI API Key:**
  ```bash
  python main.py set-key assemblyai
  ```

### Tray Icon Interaction

- **Left-click/Right-click:** Access the menu to switch providers, update credentials, or open the configuration file.
- **Icon Colors:**
  - ⚫ **Black:** Idle / Ready.
  - 🔴 **Red:** Listening...
  - 🟠 **Orange:** Error (check console or notifications).

## Configuration

The application uses `config.toml` for settings. See `config.example.toml` for a detailed template.

| Setting | Default | Description |
|---------|---------|-------------|
| `default_provider` | `openai` | Initial provider (`openai` or `assemblyai`). |
| `hotkeys.hotkey` | `ctrl+alt+v` | Global hotkey. |
| `hotkeys.hold_mode` | `true` | Hold to talk vs. Press to toggle. |
| `audio.chunk_ms` | `100` | Audio chunk size in milliseconds. |
| `providers.openai.core` | - | OpenAI model and language settings. |
| `providers.assemblyai.core`| - | AssemblyAI V3 settings and model. |
| `test.enabled` | `false` | Enable/disable mock mode. |

## License

MIT
