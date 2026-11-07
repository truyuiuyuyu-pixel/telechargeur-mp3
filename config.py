import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
DEFAULT_MUSIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Musique')

DEFAULT_CONFIG = {
    "configured": False,
    "mp3_site": "YouTube (Convertisseur MP3 haute qualité intégré)",
    "mp3_site_url": "https://www.youtube.com",
    "search_site": "YouTube Music & Moteurs de recherche",
    "search_site_url": "https://music.youtube.com",
    "music_folder": DEFAULT_MUSIC_DIR,
    "create_artist_folder": True,
    "audio_quality": "320",  # MP3 HD 320 kbps
    "auto_tag": True,
    "font_style": "font-default"
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                config = {**DEFAULT_CONFIG, **data}
                # Ensure music directory exists
                os.makedirs(config["music_folder"], exist_ok=True)
                return config
        except Exception:
            pass
    # Save default config if not exists
    os.makedirs(DEFAULT_MUSIC_DIR, exist_ok=True)
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
        if "music_folder" in cfg and cfg["music_folder"]:
            os.makedirs(cfg["music_folder"], exist_ok=True)
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la configuration: {e}")
        return False
