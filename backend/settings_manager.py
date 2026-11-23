import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SETTINGS_FILE = Path(__file__).parent.parent / 'data' / 'settings.json'

DEFAULTS = {
    'default_provider': 'pollinations',
    'default_aspect_ratio': '1:1',
    'default_style': 'realistic',
    'default_resolution': '1024x1024',
    'default_num_images': 1,
    'theme': 'dark',
    'auto_provider': True,
    'pollinations_api_key': '',
    'stability_api_key': '',
}

class SettingsManager:
    def __init__(self):
        self._settings = DEFAULTS.copy()
        self._load()
    
    def _load(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    loaded = json.load(f)
                    self._settings.update(loaded)
            except (json.JSONDecodeError, IOError):
                pass
    
    def _save(self):
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(self._settings, f, indent=2)
    
    def get(self, key, default=None):
        return self._settings.get(key, default)
    
    def get_all(self):
        return self._settings.copy()
    
    def update(self, data):
        for key, value in data.items():
            if key in DEFAULTS or key in self._settings:
                self._settings[key] = value
        self._save()
    
    def set(self, key, value):
        self._settings[key] = value
        self._save()