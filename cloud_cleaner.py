# -*- coding: utf-8 -*-
"""
cloud_cleaner.py — Gestion sécurisée du stockage temporaire du serveur
Permet au serveur de ne pas saturer son disque tout en laissant le temps à l'utilisateur
d'enregistrer ses fichiers MP3 directement sur son téléphone.
"""

import os
import time
from config import load_config

def reset_cloud_storage():
    """Nettoie les anciens fichiers audio temporaires du serveur pour libérer l'espace."""
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
        "message": f"Espace serveur libéré ({deleted_files} fichier(s) temporaire(s) nettoyé(s))."
    }

def auto_clean_old_temp_files():
    """Nettoie uniquement les fichiers temporaires créés il y a plus de 4 heures pour éviter que le disque du serveur ne se sature."""
    try:
        cfg = load_config()
        music_base = cfg.get("music_folder", "Musique")
        if not os.path.isabs(music_base):
            music_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), music_base)

        if os.path.exists(music_base):
            now = time.time()
            max_age_seconds = 4 * 3600  # 4 heures de sécurité
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
