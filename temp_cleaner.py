# -*- coding: utf-8 -*-
"""
temp_cleaner.py — Gestion sécurisée des fichiers temporaires du serveur
Nettoie les anciens fichiers de conversion temporaires pour éviter de saturer
le disque du serveur tout en garantissant que les MP3 sont envoyés directement
sur le téléphone de l'utilisateur.
"""

import os
import time
from config import load_config

def reset_temp_storage():
    """Nettoie les fichiers temporaires du serveur."""
    cfg = load_config()
    music_base = cfg.get("music_folder", "Musique")
    deleted_files = 0

    if not os.path.isabs(music_base):
        music_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), music_base)

    if os.path.exists(music_base):
        for root, dirs, files in os.walk(music_base, topdown=False):
            for file in files:
                fp = os.path.join(root, file)
                try:
                    os.remove(fp)
                    deleted_files += 1
                except Exception:
                    pass
            for d in dirs:
                dp = os.path.join(root, d)
                try:
                    if not os.listdir(dp):
                        os.rmdir(dp)
                except Exception:
                    pass

    return {
        "success": True,
        "deleted_files": deleted_files,
        "message": f"Cache serveur nettoyé ({deleted_files} fichier(s) temporaire(s))."
    }

def auto_clean_old_temp_files():
    """Nettoie automatiquement les fichiers temporaires créés il y a plus de 4 heures."""
    try:
        cfg = load_config()
        music_base = cfg.get("music_folder", "Musique")
        if not os.path.isabs(music_base):
            music_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), music_base)

        if os.path.exists(music_base):
            now = time.time()
            max_age_seconds = 4 * 3600  # 4 heures de rétention temporaire
            for root, dirs, files in os.walk(music_base, topdown=False):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        if now - os.path.getmtime(fp) > max_age_seconds:
                            os.remove(fp)
                    except Exception:
                        pass
                for d in dirs:
                    dp = os.path.join(root, d)
                    try:
                        if not os.listdir(dp):
                            os.rmdir(dp)
                    except Exception:
                        pass
    except Exception as e:
        print(f"Auto-nettoyage serveur : {e}")
