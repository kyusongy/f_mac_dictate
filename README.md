# f_mac_dictate

A lightweight voice-to-text dictation tool for macOS using Whisper AI. Hold a hotkey, speak, release, and text appears at your cursor.

## Features

- **Hold-to-talk**: Hold a key to record, release to transcribe
- **Fast transcription**: Uses Groq's Whisper API or OpenAI
- **Works everywhere**: Pastes text into any app with a text field
- **Visual feedback**: Floating indicator shows recording/processing status
- **Menu bar app**: Runs quietly in your menu bar

## Requirements

- macOS
- Python 3.10+
- Groq API key (free tier available at [groq.com](https://groq.com))

## Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/f_mac_dictate.git
cd f_mac_dictate

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

## Configuration

Edit `.env` to customize:

```env
GROQ_API_KEY=your_groq_api_key      # Required
OPENAI_API_KEY=your_openai_api_key  # Optional fallback
TRANSCRIPTION_PROVIDER=groq          # "groq" or "openai"
HOTKEY=alt_r                         # See hotkey options below
MIN_DURATION=0.5                     # Skip recordings shorter than this (seconds)
SAMPLE_RATE=16000                    # Audio sample rate
```

### Hotkey Options

- `alt_r`, `alt_l`, `alt` - Option keys
- `ctrl_r`, `ctrl_l`, `ctrl` - Control keys
- `shift_r`, `shift_l`, `shift` - Shift keys
- `cmd_r`, `cmd_l`, `cmd` - Command keys

## Usage

```bash
source .venv/bin/activate
python main.py
```

1. Grant permissions when prompted (Accessibility, Input Monitoring, Microphone)
2. Hold your configured hotkey (default: Right Option)
3. Speak
4. Release the key
5. Text appears at your cursor

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
├── transcriber.py   # Whisper API client
├── output.py        # Clipboard + paste simulation
├── indicator.py     # Floating status window
└── config.py        # Environment config loader
```


## Launch at Login

To start automatically when you log in:

1. Open **System Settings > General > Login Items**
2. Click **+** under "Open at Login"
3. Navigate to your `f_mac_dictate` folder
4. Select `main.py` (or create a wrapper script)

Alternatively, create a simple launch script:

```bash
# Create launcher script
cat > ~/Applications/dictate.command << 'EOF'
#!/bin/bash
cd ~/path/to/f_mac_dictate
source .venv/bin/activate
python main.py
EOF
chmod +x ~/Applications/dictate.command
```

Then add `dictate.command` to your Login Items.

## License

MIT
