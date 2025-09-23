
# Downloader Telegram Bot 🤖

![Статус](https://img.shields.io/badge/status-active-brightgreen)
![Версия](https://img.shields.io/badge/version-1.0.0-blue)
[![Лицензия](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.22.0-blue)](https://docs.aiogram.dev/)

**Telegram bot for downloading media content from links.
Just send a link — the bot will handle the rest.**

---

## ✨ Features

- **📹 YouTube Video:** download videos from YouTube in high quality
- **🎵 YouTube Shorts:** download short videos from YouTube Shorts  
- **📱 TikTok Video:** download videos from TikTok without watermarks
- **🎧 SoundCloud Music:** download music and tracks from SoundCloud  
- **📊 Detailed logging:** all user actions and bot processes are recorded for debugging and analysis  

---

## 🛠 Technologies

- **Python 3.13** — main programming language 
- **Aiogram 3.22.0** — asynchronous framework for Telegram Bot API

---

## 📦 Installation and Running

### 1. Clone the repository
```bash
git clone https://github.com/hejmua/downloader-bot.git
```

### 2. Add folder Tools in the root folder
- Download last release build from:
```bash
https://www.gyan.dev/ffmpeg/builds/
```
- Open the ZIP archive and extract the .exe files from the bin folder into tools, so that you end up with:
```bash
├── tools/                
│   ├── ffmpeg.exe        
│   ├── ffplay.exe        
│   └── ffprobe.exe
```

### 3. Create and activate a virtual environment (recommended)
```bash
# For Linux/macOS
python -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
venv\Scripts\activate
```

### 4. Install the dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure the bot token
- Create a .env file in the root directory of the project:
```bash
BOT_TOKEN=your_telegram_bot_token_here
```
- Or specify the token directly in main.py:
```bash
bot = Bot(token="your_actual_bot_token_here")
```

### 6. Run the bot
```bash
python main.py
```

---

## 📁 Project structure
```bash
downloader-bot/
├── downloaders/          # Modules for downloading from different platforms
│   ├── soundcloud.py     # Downloader for SoundCloud
│   ├── tiktok.py         # Downloader for TikTok
│   └── youtube.py        # Downloader for YouTube and Shorts
├── tools/                # Helper utilities
│   ├── ffmpeg.exe        # Media processing
│   ├── ffplay.exe        # Player
│   └── ffprobe.exe       # Media file information
├── main.py               # Main bot file
├── requirements.txt      # Project dependencies
├── bot.log               # Logs
├── .env                  # Environment variables (to be created)
├── LICENSE               # MIT License
└── README.md             # Documentation
```

---

# ⚠️ Important

- ### The bot is intended for personal use
- ### Make sure you have the rights to the content you are downloading