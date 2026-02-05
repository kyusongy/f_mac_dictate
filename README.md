# f_mac_dictate

A lightweight voice-to-text dictation tool for macOS using Whisper AI. Hold a hotkey, speak, release, and text appears at your cursor.

## Features

- **Hold-to-talk**: Hold a key to record, release to transcribe
- **Fast transcription**: Uses Groq's Whisper API or OpenAI
- **Works everywhere**: Pastes text into any app with a text field
- **Visual feedback**: Floating indicator shows recording/processing/error status
- **Menu bar app**: Runs quietly in your menu bar with hotkey label
- **Connection reuse**: Persistent HTTP connections for faster repeat transcriptions
- **Whisper prompt**: Guide transcription style/vocabulary via `WHISPER_PROMPT`

## Requirements

- macOS
- Python 3.10+
- Groq API key (free tier available at [groq.com](https://groq.com))

## Installation

```bash
git clone https://github.com/kyusongy/f_mac_dictate.git
cd f_mac_dictate
make install

# Configure
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

Or manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Edit `.env` to customize:

```env
GROQ_API_KEY=your_groq_api_key      # Required for Groq
OPENAI_API_KEY=your_openai_api_key  # Required for OpenAI
TRANSCRIPTION_PROVIDER=groq          # "groq" or "openai"
HOTKEY=alt_r                         # See hotkey options below
MIN_DURATION=0.5                     # Skip recordings shorter than this (seconds)
SAMPLE_RATE=16000                    # Audio sample rate
WHISPER_MODEL=                       # Defaults per provider (whisper-large-v3-turbo / whisper-1)
WHISPER_PROMPT=                      # Optional prompt to guide transcription
```

Invalid config values fall back to defaults with a stderr warning.

### Hotkey Options

- `alt_r`, `alt_l`, `alt` - Option keys
- `ctrl_r`, `ctrl_l`, `ctrl` - Control keys
- `shift_r`, `shift_l`, `shift` - Shift keys
- `cmd_r`, `cmd_l`, `cmd` - Command keys

## Usage

```bash
make run
```

Or manually:

```bash
source .venv/bin/activate
python main.py
```

1. Grant permissions when prompted (Accessibility, Input Monitoring, Microphone)
2. Hold your configured hotkey (default: Right Option)
3. Speak
4. Release the key
5. Text appears at your cursor

Too-short recordings show a brief "Too short" indicator. Transcription errors display in the indicator instead of pasting into your document.

## macOS Permissions

The app requires these permissions in **System Settings > Privacy & Security**:

- **Accessibility**: For simulating keyboard paste
- **Input Monitoring**: For global hotkey detection
- **Microphone**: For audio recording

## Architecture

```
f_mac_dictate/
├── main.py          # Menu bar app entry point
├── hotkey.py        # Global hotkey listener
├── recorder.py      # Audio capture
├── transcriber.py   # Whisper API client (persistent connections)
├── output.py        # Clipboard + paste simulation
├── indicator.py     # Floating status window
├── config.py        # Environment config loader + validation
├── Makefile         # Install, run, bundle, launchagent targets
├── setup.py         # py2app bundle config
└── com.f_mac_dictate.plist  # LaunchAgent for auto-start
```

## Bundling

Build a standalone `.app` bundle:

```bash
make bundle
```

## Launch at Login

Using the LaunchAgent:

```bash
make launchagent
```

Or manually: open **System Settings > General > Login Items** and add the `.app` bundle or a wrapper script.

## License

MIT
