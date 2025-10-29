# 🎧 Mediacorp Radio Station

A simple **Discord bot** that streams live Singapore radio stations into your discord voice channel using FFmpeg.

## 🚀 Features

- 🔊 Stream popular radio stations directly into your Discord voice channel  
- 🧠 Commands for easy control (`!play`, `!stop`, `!cmds`)  
- 🎶 Auto reconnects to streams if disconnected  
- 💬 Works with any Discord voice channel  

---

## 🧩 Available Stations

| Command | Station |
|----------|----------|
| `987` | 987 FM |
| `yes933` | YES 933 |
| `class95` | CLASS 95 |
| `love972` | LOVE 972 |
| `capital958` | CAPITAL 958 |
| `cna938` | CNA 938 |

---

## ⚙️ Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/yourusername/discord-radio-bot.git
cd discord-radio-bot
```

### 2️⃣ Create and activate a virtual environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate  # on macOS/Linux
venv\Scripts\activate     # on Windows
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```
Or manually install:
```bash
pip install discord.py python-dotenv requests
```

### 4️⃣ Install FFmpeg
You must have FFmpeg installed and available in your system PATH.

Windows: Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip)

macOS: 
```bash
brew install ffmpeg
```

Linux:
```bash
sudo apt install ffmpeg
```

### 🔐 Environment Setup
Rename the .env.example to .env, replace the placeholder with your bot token
```ini
DISCORD_TOKEN=your_discord_bot_token_here
```

### ▶️ Usage
Run the bot:
```bash
python main.py
```

In Discord:
```yaml
!cmds                # Show help
!play <station>      # Play a station (e.g. !play yes933)
!stop                # Stop playback and leave voice channel
```

### 🧠 Notes
- The bot requires message content intent enabled in your [Discord Developer Portal](https://discord.com/developers/applications).
- The FFmpeg binary must be installed and accessible in your System PATH.
- Some stations may occasionally change their stream URLs. Update the stations dictionary if that happens.

### 🪪 License
MIT License © 2025 Nekolabs Inc.