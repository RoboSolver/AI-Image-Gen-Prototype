# Local AI Image Generator

A lightweight, browser-based AI image generator that runs locally and uses remote APIs for generation.

## Features

- Text-to-image generation via Pollinations API (free tier available)
- 1-9 images per request
- Multiple aspect ratios and styles
- Dark/light theme
- Generation history with SQLite
- Local image storage
- Provider fallback architecture (extensible)

## Quick Start

### Prerequisites

- Python 3.11+
- Pollinations API key (free from [enter.pollinations.ai](https://enter.pollinations.ai))

### Installation

```bash
# Clone and enter directory
cd AI-Image-Generator

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Windows CMD)
venv\Scripts\activate.bat

# Activate (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and add your API key
copy .env.example .env
# Edit .env and add your POLLINATIONS_API_KEY
```

### Run

```bash
python app.py
```

The app will open at `http://localhost:5000` in your default browser.

## Project Structure

```
AI-Image-Generator/
├── app.py                 # Flask entry point
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── .gitignore            # Git ignore rules
├── README.md             # This file
├── backend/              # Backend modules
│   ├── generator.py      # Generation orchestration
│   ├── provider_manager.py # Provider selection/fallback
│   ├── database.py       # SQLite history
│   ├── settings_manager.py # User settings
│   └── image_manager.py  # Image file handling
├── providers/            # Provider implementations
│   ├── base_provider.py  # Abstract base class
│   └── pollinations.py   # Pollinations provider
├── templates/            # HTML templates
│   ├── index.html        # Main page
│   ├── settings.html     # Settings page
│   └── history.html      # History page
├── static/               # Static assets
│   ├── css/style.css     # Styles (dark/light themes)
│   └── js/app.js         # Frontend logic
├── data/                 # Local data (gitignored)
│   ├── history.db        # SQLite database
│   └── settings.json     # User preferences
└── generated_images/     # Generated images (gitignored)
    └── YYYY-MM-DD/
        └── image_XXX.png
```

## Configuration

Edit `.env` file:

```env
POLLINATIONS_API_KEY=sk_your_key_here
FLASK_SECRET_KEY=your-random-secret
FLASK_PORT=5000
DEFAULT_PROVIDER=pollinations
DEFAULT_ASPECT_RATIO=1:1
DEFAULT_STYLE=realistic
DEFAULT_RESOLUTION=1024x1024
DEFAULT_NUM_IMAGES=1
```

## API Providers

Currently implemented:
- **Pollinations** (primary) - Free `flux` model, optional API key for higher limits

Planned:
- Stability AI
- Cloudflare Workers AI

## License

MIT