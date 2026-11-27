# -*- coding: utf-8 -*-
"""
downloader.py — Moteur universel de téléchargement MP3 multi-sources
Prend en charge :
- Tous les sites de musique : YouTube, YouTube Music, SoundCloud, Bandcamp, Jamendo, Audiomack, TikTok, etc.
- Liens directs vers des fichiers MP3 / audio (.mp3, .m4a, .wav, .flac, .ogg)
- Recherche simultanée multi-sites (YouTube + SoundCloud)
- Encodage MP3 HD 320 kbps (ou qualité choisie)
- Dossiers automatiques par chanteur
- Tags ID3 complets (Artiste, Titre, Album, Pochette)
- Téléchargement par Thème & Discographie complète
"""

import os
import sys
import time
import shutil
import tempfile
import threading
import uuid
import re
import urllib.parse
import requests
import yt_dlp
import imageio_ffmpeg

from config import load_config
from music_tagger import (
    sanitize_filename,
    clean_noise_from_title,
    clean_artist_name,
    parse_artist_and_title,
    tag_mp3,
    read_mp3_tags
)
import themes

# Suivi des tâches de téléchargement actives
ACTIVE_DOWNLOADS = {}

def get_ffmpeg_path():
    """Récupère le chemin exécutable de ffmpeg (système ou imageio-ffmpeg)."""
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as e:
        print(f"Avertissement ffmpeg : {e}")
        return None

def format_duration(seconds):
    """Formate les secondes en MM:SS."""
    if not seconds:
        return "00:00"
    try:
        sec = int(seconds)
        m = sec // 60
        s = sec % 60
        return f"{m:02d}:{s:02d}"
    except Exception:
        return "00:00"

def is_direct_audio_url(url: str) -> bool:
    """Vérifie si l'URL pointe directement vers un fichier audio."""
    clean_url = url.split("?")[0].lower()
    return clean_url.endswith((".mp3", ".m4a", ".wav", ".ogg", ".flac", ".aac", ".opus", ".wma"))

def pick_best_studio_track(entries, expected_artist="", expected_title="", user_query=""):
    """
    Sélectionne la piste audio la plus propre et officielle :
    - Privilégie les pistes lyrics / paroles (sans bruits de clip vidéo)
    - Privilégie les chaînes officielles Topic / Official Audio
    - Ne pénalise pas les mots si l'utilisateur les a demandés expressément
    """
    if not entries:
        return None

    user_q_lower = (user_query or expected_title or "").lower()

    def calculate_score(entry):
        if not entry:
            return -999
        title = (entry.get('title') or '').lower()
        uploader = (entry.get('uploader') or entry.get('channel') or '').lower()
        duration = entry.get('duration') or 0
        score = 50

        bad_words = [
            'interview', 'parodie', 'parody', 'reaction', 'react', 'court métrage',
            'short film', 'behind the scenes', 'making of', 'teaser', 'trailer', 'vlog'
        ]
        for w in bad_words:
            if w in title and w not in user_q_lower:
                score -= 70

        # Mots spécifiques (remix, live, karaoke, instrumental) : ne pénaliser que si l'utilisateur ne les a pas cherchés
        musical_specs = ['live', 'concert', 'acoustic', 'karaoke', 'remix', 'instrumental']
        for spec in musical_specs:
            if spec in title and spec not in user_q_lower:
                score -= 40

        # Priorité aux paroles / lyrics (audio studio pur)
        if 'lyrics' in title or 'lyric' in title or 'paroles' in title:
            score += 80

        # Priorité audio officiel / Topic
        if ' - topic' in uploader or 'topic' in uploader:
            score += 60
        if 'official audio' in title or 'audio officiel' in title or '(audio)' in title or '[audio]' in title:
            score += 50
        if 'provided to youtube' in (entry.get('description') or '').lower():
            score += 45

        # Correspondance du chanteur
        if expected_artist and expected_artist.lower() in uploader:
            score += 30

        # Durée typique de chanson (1m20 à 7min)
        if 80 <= duration <= 420:
            score += 20
        elif duration < 45 or duration > 900:
            score -= 30

        return score

    sorted_entries = sorted(entries, key=calculate_score, reverse=True)
    return sorted_entries[0] if sorted_entries else None

def get_yt_dlp_common_opts():
    """Options yt-dlp robustes avec compatibilité maximale (PC local et serveurs cloud / Linux)."""
    return {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'hls_prefer_native': True,
        'socket_timeout': 25,
        'retries': 6,
        'fragment_retries': 6,
    }

def search_tracks(query: str, limit: int = 12, source: str = "all"):
    """
    Recherche des morceaux sur TOUS les sites de musique :
    - YouTube / YouTube Music
    - SoundCloud
    - Liens directs / Sites MP3
    """
    results = []
    clean_q = query.strip()
    if not clean_q:
        return results

    # 1. CAS D'UN LIEN DIRECT OU SITE MP3
    if clean_q.startswith("http://") or clean_q.startswith("https://"):
        try:
            # Si c'est un fichier MP3 direct
            if is_direct_audio_url(clean_q):
                parsed = urllib.parse.urlparse(clean_q)
                fname = os.path.basename(parsed.path)
                fname_clean = os.path.splitext(fname)[0]
                art, tit = parse_artist_and_title(fname_clean)
                return [{
                    "id": str(uuid.uuid4())[:8],
                    "url": clean_q,
                    "raw_title": fname,
                    "title": tit or fname_clean,
                    "artist": art or "Direct MP3",
                    "uploader": parsed.netloc,
                    "duration": "--:--",
                    "duration_sec": 0,
                    "thumbnail": "",
                    "source": "Lien Direct MP3"
                }]

            # Sinon analyse via yt-dlp (gère +1000 sites dont YouTube, SoundCloud, Bandcamp, TikTok...)
            opts = get_yt_dlp_common_opts()
            opts['extract_flat'] = True
            opts['noplaylist'] = True

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(clean_q, download=False)
                if info:
                    raw_title = info.get('title', 'Musique')
                    uploader = info.get('uploader') or info.get('channel') or info.get('creator', '')
                    art_meta = info.get('artist')
                    trk_meta = info.get('track')

                    artist, title = parse_artist_and_title(raw_title, uploader, art_meta, trk_meta)
                    extractor = (info.get('extractor_key') or "Web Music").capitalize()

                    thumb = info.get('thumbnail', '')
                    if not thumb and info.get('thumbnails'):
                        thumb = info.get('thumbnails')[-1].get('url', '')

                    return [{
                        "id": info.get('id', str(uuid.uuid4())[:8]),
                        "url": clean_q,
                        "raw_title": raw_title,
                        "title": title,
                        "artist": artist,
                        "uploader": uploader or extractor,
                        "duration": format_duration(info.get('duration', 0)),
                        "duration_sec": info.get('duration', 0),
                        "thumbnail": thumb,
                        "source": f"Site : {extractor}"
                    }]
        except Exception as e:
            print(f"Erreur extraction URL directe : {e}")

    # 2. RECHERCHE TEXTUELLE MULTI-SOURCES (YouTube + SoundCloud)
    seen_ids = set()

    # Recherche YouTube (si source "all" ou "youtube")
    if source in ("all", "youtube"):
        try:
            yt_opts = get_yt_dlp_common_opts()
            yt_opts['extract_flat'] = True
            yt_opts['noplaylist'] = True

            yt_query = f"ytsearch{limit}:{clean_q}"
            with yt_dlp.YoutubeDL(yt_opts) as ydl:
                res = ydl.extract_info(yt_query, download=False)
                entries = res.get('entries', []) if res else []

                for entry in entries:
                    if not entry:
                        continue
                    eid = entry.get('id')
                    if eid in seen_ids:
                        continue
                    seen_ids.add(eid)

                    raw_title = entry.get('title', '')
                    uploader = entry.get('uploader') or entry.get('channel', '')
                    art, tit = parse_artist_and_title(raw_title, uploader, entry.get('artist'), entry.get('track'))

                    thumb = entry.get('thumbnail', '')
                    if not thumb and entry.get('thumbnails'):
                        thumb = entry.get('thumbnails')[-1].get('url', '')

                    url = entry.get('url') or entry.get('webpage_url')
                    if not url and eid:
                        url = f"https://www.youtube.com/watch?v={eid}"
                    if not url or any(bad in url for bad in ('/channel/', '/user/', '/@', '/playlist?')):
                        continue

                    results.append({
                        "id": eid or str(uuid.uuid4())[:8],
                        "url": url,
                        "raw_title": raw_title,
                        "title": tit,
                        "artist": art,
                        "uploader": uploader,
                        "duration": format_duration(entry.get('duration', 0)),
                        "duration_sec": entry.get('duration', 0),
                        "thumbnail": thumb,
                        "source": "YouTube Music"
                    })
        except Exception as e:
            print(f"Erreur recherche YouTube : {e}")

    # Recherche SoundCloud (si source "all" ou "soundcloud")
    if source in ("all", "soundcloud"):
        try:
            sc_limit = limit if source == "soundcloud" else max(3, limit // 2)
            sc_opts = get_yt_dlp_common_opts()
            sc_opts['extract_flat'] = True
            sc_opts['noplaylist'] = True

            sc_query = f"scsearch{sc_limit}:{clean_q}"
            with yt_dlp.YoutubeDL(sc_opts) as ydl:
                res = ydl.extract_info(sc_query, download=False)
                entries = res.get('entries', []) if res else []

                for entry in entries:
                    if not entry:
                        continue
                    dur_sc = entry.get('duration') or 0
                    if 0 < dur_sc <= 35:
                        # Ignorer les aperçus SoundCloud Go+ de 30s protégés par DRM
                        continue
                    eid = f"sc_{entry.get('id')}"
                    if eid in seen_ids:
                        continue
                    seen_ids.add(eid)

                    raw_title = entry.get('title', '')
                    uploader = entry.get('uploader') or 'SoundCloud'
                    art, tit = parse_artist_and_title(raw_title, uploader)

                    thumb = entry.get('thumbnail', '')
                    if not thumb and entry.get('thumbnails'):
                        thumb = entry.get('thumbnails')[-1].get('url', '')

                    url = entry.get('url') or entry.get('webpage_url')

                    results.append({
                        "id": eid,
                        "url": url,
                        "raw_title": raw_title,
                        "title": tit,
                        "artist": art,
                        "uploader": uploader,
                        "duration": format_duration(entry.get('duration', 0)),
                        "duration_sec": entry.get('duration', 0),
                        "thumbnail": thumb,
                        "source": "SoundCloud MP3"
                    })
        except Exception as e:
            print(f"Erreur recherche SoundCloud : {e}")

    return results

def _extract_yt_id(url: str):
    if not url:
        return None
    m = re.search(r'(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})', url)
    return m.group(1) if m else None


def _download_via_piped(video_id: str, temp_dir: str):
    """Fallback cloud via instances Piped publiques si YouTube bloque l'IP."""
    if not video_id:
        return None
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.adminforge.de",
        "https://api.piped.private.coffee",
        "https://pipedapi.leptons.xyz",
    ]
    for base in instances:
        try:
            r = requests.get(f"{base}/streams/{video_id}", timeout=8)
            if r.status_code != 200:
                continue
            data = r.json()
            streams = data.get("audioStreams") or []
            if not streams:
                continue
            best = max(streams, key=lambda s: s.get("bitrate", 0))
            stream_url = best.get("url")
            if not stream_url:
                continue
            ext = "m4a" if "mp4" in (best.get("mimeType") or "") else "webm"
            out_path = os.path.join(temp_dir, f"{video_id}.{ext}")
            resp = requests.get(stream_url, stream=True, timeout=25)
            if resp.status_code != 200:
                continue
            with open(out_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
            if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
                return {"title": data.get("title", ""), "artist": data.get("uploader", ""), "thumbnail": data.get("thumbnailUrl", "")}
        except Exception:
            continue
    return None


def process_single_track(url: str, chosen_artist: str = "", chosen_title: str = "", album: str = None, cover_url: str = None, progress_hook_cb = None):
    """
    Télécharge et convertit un morceau en MP3 HD 320k avec tags ID3 complets.
    Place le fichier directement dans Musique/{Artiste}/{Titre}.mp3.
    """
    temp_dir = tempfile.mkdtemp(prefix="mp3_task_")
    try:
        cfg = load_config()
        music_base = cfg.get("music_folder", "Musique")
        create_folder_per_artist = cfg.get("create_artist_folder", True)
        audio_quality = cfg.get("audio_quality", "320")
        ffmpeg_path = get_ffmpeg_path()

        final_artist = sanitize_filename(chosen_artist) if chosen_artist else "Artiste Inconnu"
        final_title = sanitize_filename(chosen_title) if chosen_title else "Sans Titre"
        final_album = album if album else f"{final_artist} Singles"

        downloaded_audio_path = None
        effective_cover = cover_url

        # --- CAS A : Fichier MP3 / audio direct ---
        if url.startswith("http") and is_direct_audio_url(url):
            if progress_hook_cb:
                progress_hook_cb(30, "Téléchargement direct du fichier MP3...")
            direct_file = os.path.join(temp_dir, f"source_{int(time.time())}.mp3")
            resp = requests.get(url, stream=True, timeout=30)
            resp.raise_for_status()
            with open(direct_file, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
            downloaded_audio_path = direct_file

        # --- CAS B : URL web (YouTube, SoundCloud, Bandcamp...) ou recherche ---
        else:
            effective_url = url
            # Si c'est un texte de recherche sans protocole HTTP
            if not (url.startswith("http://") or url.startswith("https://")):
                search_str = f"ytsearch5:{url}"
                try:
                    with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True, 'noplaylist': True}) as ydl_s:
                        s_res = ydl_s.extract_info(search_str, download=False)
                        entries = s_res.get('entries', []) if s_res else []
                        best = pick_best_studio_track(entries, chosen_artist, chosen_title, url)
                        if best:
                            effective_url = best.get('url') or best.get('webpage_url') or f"https://www.youtube.com/watch?v={best.get('id')}"
                except Exception as ex_s:
                    print(f"Recherche YT initiale échouée : {ex_s}")

            def progress_hook(d):
                if progress_hook_cb:
                    if d.get('status') == 'downloading':
                        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                        downloaded = d.get('downloaded_bytes') or 0
                        if total > 0:
                            pct = int((downloaded / total) * 75)
                            progress_hook_cb(max(10, min(pct, 75)), f"Téléchargement audio : {pct}%")
                    elif d.get('status') == 'finished':
                        progress_hook_cb(80, "Conversion en MP3 HD 320k (FFmpeg)...")

            out_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
            ydl_opts = get_yt_dlp_common_opts()
            ydl_opts.update({
                'format': 'bestaudio*/best',
                'outtmpl': out_template,
                'progress_hooks': [progress_hook],
                'noplaylist': True,
            })

            if ffmpeg_path:
                ydl_opts['ffmpeg_location'] = ffmpeg_path
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': audio_quality,
                }]
                ydl_opts['postprocessor_args'] = {
                    'ffmpegextractaudio': ['-b:a', f'{audio_quality}k', '-ar', '44100']
                }

            # Tentative principale + fallbacks multi-sources (clients YT alternatifs, YT audio, SoundCloud)
            info = None
            fallback_query = f"{chosen_artist} {chosen_title}".strip()
            if not fallback_query or fallback_query in ("Artiste Inconnu", "Sans Titre", "Artiste Inconnu Sans Titre"):
                fallback_query = url if not (url.startswith("http://") or url.startswith("https://")) else ""

            attempts = [
                ("Source principale", effective_url, ydl_opts),
            ]
            if fallback_query:
                attempts.append(("YouTube Audio", f"ytsearch1:{fallback_query}", ydl_opts))
                attempts.append(("YouTube Lyrics", f"ytsearch1:{fallback_query} lyrics", ydl_opts))
                attempts.append(("SoundCloud", f"scsearch1:{fallback_query}", ydl_opts))

            alt_opts = dict(ydl_opts)
            alt_opts['extractor_args'] = {'youtube': {'player_client': ['mweb', 'web_safari']}}
            attempts.append(("Client alternatif", effective_url, alt_opts))

            last_err = None
            for label, target_src, opts_try in attempts:
                try:
                    if label != "Source principale" and progress_hook_cb:
                        progress_hook_cb(45, f"Nouvelle tentative ({label})...")
                    with yt_dlp.YoutubeDL(opts_try) as ydl_try:
                        info = ydl_try.extract_info(target_src, download=True)
                    if info:
                        if 'entries' in info and info['entries']:
                            info = info['entries'][0]
                        break
                except Exception as ex_try:
                    last_err = ex_try
                    print(f"Échec {label} ({target_src}) : {ex_try}")
                    info = None

            if not info and not os.listdir(temp_dir):
                yt_id = _extract_yt_id(effective_url)
                if yt_id:
                    if progress_hook_cb:
                        progress_hook_cb(55, "Source miroir Piped en cours...")
                    info = _download_via_piped(yt_id, temp_dir)

            if not info and not os.listdir(temp_dir):
                raise Exception(f"Impossible de télécharger ce morceau ({last_err})")

            if info and not effective_cover:
                effective_cover = info.get('thumbnail')
                if not effective_cover and info.get('thumbnails'):
                    effective_cover = info.get('thumbnails')[-1].get('url')

            if info:
                if (not chosen_artist or chosen_artist == "Artiste Inconnu"):
                    ext_a = info.get('artist') or info.get('uploader') or ""
                    if ext_a:
                        final_artist = sanitize_filename(ext_a)
                if (not chosen_title or chosen_title == "Sans Titre"):
                    ext_t = info.get('track') or info.get('title') or ""
                    if ext_t:
                        final_title = sanitize_filename(ext_t)
                if not album:
                    final_album = f"{final_artist} Singles"

            # Récupération du fichier généré
            for f in os.listdir(temp_dir):
                if f.lower().endswith(".mp3"):
                    downloaded_audio_path = os.path.join(temp_dir, f)
                    break

            if not downloaded_audio_path:
                files = os.listdir(temp_dir)
                if files:
                    downloaded_audio_path = os.path.join(temp_dir, files[0])
                else:
                    raise Exception("Aucun fichier audio n'a pu être extrait.")

        # --- CAS C : Encodage direct en MP3 si nécessaire ---
        if downloaded_audio_path and not downloaded_audio_path.lower().endswith(".mp3"):
            if progress_hook_cb:
                progress_hook_cb(85, "Encodage MP3 HD...")
            mp3_converted = os.path.join(temp_dir, f"{final_title}.mp3")
            if ffmpeg_path:
                import subprocess
                cmd = [ffmpeg_path, "-y", "-i", downloaded_audio_path, "-b:a", f"{audio_quality}k", "-ar", "44100", mp3_converted]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                downloaded_audio_path = mp3_converted

        if progress_hook_cb:
            progress_hook_cb(90, "Application des tags ID3 (Chanteur, Titre)...")

        # 1. Écriture des tags ID3
        try:
            tag_mp3(
                file_path=downloaded_audio_path,
                artist=final_artist,
                title=final_title,
                album=final_album,
                cover_url=effective_cover
            )
        except Exception as e_tag:
            print(f"Avertissement tag MP3 : {e_tag}")

        # 2. Dossier par chanteur
        if create_folder_per_artist:
            dest_dir = os.path.join(music_base, final_artist)
        else:
            dest_dir = music_base

        os.makedirs(dest_dir, exist_ok=True)

        target_filename = f"{final_title}.mp3"
        target_path = os.path.join(dest_dir, target_filename)

        # Éviter l'écrasement en cas de doublon
        counter = 1
        base_target = os.path.splitext(target_path)[0]
        while os.path.exists(target_path):
            target_filename = f"{final_title} ({counter}).mp3"
            target_path = f"{base_target} ({counter}).mp3"
            counter += 1

        shutil.move(downloaded_audio_path, target_path)
        rel_path = os.path.relpath(target_path, music_base).replace("\\", "/")

        return target_path, target_filename, rel_path, final_artist, final_title
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def download_single_track_sync(url: str, chosen_artist: str = "", chosen_title: str = "", album: str = None, cover_url: str = None):
    """
    Téléchargement 100% direct et immédiat pour envoi direct dans la mémoire du téléphone.
    """
    target_path, target_filename, rel_path, final_artist, final_title = process_single_track(
        url, chosen_artist, chosen_title, album, cover_url
    )
    return target_path, target_filename

def download_track_async(url: str, chosen_artist: str, chosen_title: str, album: str = None, cover_url: str = None, task_id: str = None):
    """
    Télécharge et convertit en MP3 HD 320k en tâche de fond.
    Sauvegarde dans Musique/{Artiste}/{Titre}.mp3 avec tags ID3.
    Garantit que le fichier est disponible pour le téléchargement direct sur téléphone/PC.
    """
    if not task_id:
        task_id = str(uuid.uuid4())

    ACTIVE_DOWNLOADS[task_id] = {
        "id": task_id,
        "status": "starting",
        "progress": 0,
        "artist": chosen_artist or "Artiste Inconnu",
        "title": chosen_title or "Sans Titre",
        "message": "Démarrage du téléchargement...",
        "filepath": None,
        "filename": None,
        "rel_path": None,
        "error": None
    }

    def _worker():
        try:
            ACTIVE_DOWNLOADS[task_id]["status"] = "downloading"
            def hook_cb(pct, msg):
                ACTIVE_DOWNLOADS[task_id]["progress"] = pct
                ACTIVE_DOWNLOADS[task_id]["message"] = msg

            target_path, target_filename, rel_path, final_artist, final_title = process_single_track(
                url, chosen_artist, chosen_title, album, cover_url, progress_hook_cb=hook_cb
            )

            ACTIVE_DOWNLOADS[task_id]["status"] = "completed"
            ACTIVE_DOWNLOADS[task_id]["progress"] = 100
            ACTIVE_DOWNLOADS[task_id]["message"] = f"✅ Téléchargé avec succès ! Prêt pour votre téléphone."
            ACTIVE_DOWNLOADS[task_id]["filepath"] = target_path
            ACTIVE_DOWNLOADS[task_id]["filename"] = target_filename
            ACTIVE_DOWNLOADS[task_id]["rel_path"] = rel_path
            ACTIVE_DOWNLOADS[task_id]["artist"] = final_artist
            ACTIVE_DOWNLOADS[task_id]["title"] = final_title

        except Exception as e:
            print(f"Erreur téléchargement tâche {task_id} : {e}")
            ACTIVE_DOWNLOADS[task_id]["status"] = "error"
            ACTIVE_DOWNLOADS[task_id]["error"] = str(e)
            ACTIVE_DOWNLOADS[task_id]["message"] = f"Erreur : {e}"

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return task_id

def download_theme_async(theme_id: str, task_id: str = None):
    """
    Télécharge TOUTES les musiques d'un thème musical complet en tâche de fond.
    Crée les dossiers par chanteur, applique les tags ID3 officiels.
    """
    theme_info = themes.get_theme_by_id(theme_id)
    if not theme_info:
        raise ValueError(f"Thème introuvable : {theme_id}")

    tracks = theme_info.get("tracks", [])
    if not task_id:
        task_id = str(uuid.uuid4())

    total = len(tracks)

    ACTIVE_DOWNLOADS[task_id] = {
        "id": task_id,
        "type": "theme_batch",
        "theme_id": theme_id,
        "theme_name": theme_info.get("name", "Thème"),
        "status": "starting",
        "progress": 0,
        "total_tracks": total,
        "completed_tracks": 0,
        "current_track": "",
        "message": f"Démarrage du téléchargement du thème {theme_info.get('name')} ({total} titres)...",
        "error": None
    }

    def _theme_worker():
        completed = 0
        cfg = load_config()
        music_base = cfg.get("music_folder", "Musique")
        audio_quality = cfg.get("audio_quality", "320")
        ffmpeg_path = get_ffmpeg_path()

        for idx, tr in enumerate(tracks, 1):
            title = tr.get("title", "")
            artist = tr.get("artist", "")
            query = tr.get("query", f"{artist} {title} lyrics")

            ACTIVE_DOWNLOADS[task_id]["status"] = "downloading"
            ACTIVE_DOWNLOADS[task_id]["current_track"] = f"{artist} — {title}"
            ACTIVE_DOWNLOADS[task_id]["completed_tracks"] = completed
            ACTIVE_DOWNLOADS[task_id]["message"] = f"[{idx}/{total}] Téléchargement : {artist} — {title}..."

            temp_dir = tempfile.mkdtemp(prefix="theme_dl_")
            try:
                out_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
                ydl_opts = get_yt_dlp_common_opts()
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'outtmpl': out_template,
                    'noplaylist': True,
                })
                if ffmpeg_path:
                    ydl_opts['ffmpeg_location'] = ffmpeg_path
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': audio_quality,
                    }]
                    ydl_opts['postprocessor_args'] = {
                        'ffmpegextractaudio': ['-b:a', f'{audio_quality}k', '-ar', '44100']
                    }

                search_query = f"ytsearch1:{query}"
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(search_query, download=True)
                    entries = info.get('entries', []) if info else []
                    vid_info = entries[0] if entries else info

                # Récupérer MP3
                downloaded_file = None
                for f in os.listdir(temp_dir):
                    if f.lower().endswith(".mp3"):
                        downloaded_file = os.path.join(temp_dir, f)
                        break

                if downloaded_file:
                    clean_art = sanitize_filename(artist)
                    clean_tit = sanitize_filename(title)
                    dest_dir = os.path.join(music_base, clean_art)
                    os.makedirs(dest_dir, exist_ok=True)

                    tag_mp3(
                        file_path=downloaded_file,
                        artist=clean_art,
                        title=clean_tit,
                        album=f"Thème {theme_info.get('name')}",
                        cover_url=vid_info.get('thumbnail') if vid_info else None
                    )

                    target_path = os.path.join(dest_dir, f"{clean_tit}.mp3")
                    counter = 1
                    base_target = os.path.splitext(target_path)[0]
                    while os.path.exists(target_path):
                        target_path = f"{base_target} ({counter}).mp3"
                        counter += 1

                    shutil.move(downloaded_file, target_path)
                    completed += 1

            except Exception as e_tr:
                print(f"Erreur téléchargement morceau de thème {title} : {e_tr}")
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

            pct = int((idx / total) * 100)
            ACTIVE_DOWNLOADS[task_id]["progress"] = pct
            ACTIVE_DOWNLOADS[task_id]["completed_tracks"] = completed

        ACTIVE_DOWNLOADS[task_id]["status"] = "completed"
        ACTIVE_DOWNLOADS[task_id]["progress"] = 100
        ACTIVE_DOWNLOADS[task_id]["message"] = f"🎉 Thème {theme_info.get('name')} téléchargé avec succès ({completed}/{total} titres prêts) !"

    thread = threading.Thread(target=_theme_worker, daemon=True)
    thread.start()
    return task_id

def download_singer_discography_async(artist_name: str, tracks: list, skip_duplicates: bool = False, task_id: str = None):
    """
    Télécharge la discographie complète d'un artiste en tâche de fond.
    """
    if not task_id:
        task_id = str(uuid.uuid4())

    filtered_tracks = []
    skipped_count = 0
    for t in tracks:
        if skip_duplicates and t.get("is_duplicate"):
            skipped_count += 1
        else:
            filtered_tracks.append(t)

    # Si tous ont été ignorés mais qu'on a des pistes, prendre toutes les pistes pour ne pas avoir 0
    if not filtered_tracks and tracks:
        filtered_tracks = tracks
        skipped_count = 0

    ACTIVE_DOWNLOADS[task_id] = {
        "id": task_id,
        "type": "batch_singer",
        "artist": artist_name,
        "status": "starting",
        "progress": 0,
        "total_tracks": len(filtered_tracks),
        "completed_tracks": 0,
        "skipped_duplicates": skipped_count,
        "current_track": "",
        "message": f"Démarrage : {len(filtered_tracks)} titres à télécharger...",
        "error": None
    }

    def _batch_worker():
        from scanner import create_artist_files_and_playlist
        total = len(filtered_tracks)
        completed = 0

        create_artist_files_and_playlist(artist_name, tracks)

        if total == 0:
            ACTIVE_DOWNLOADS[task_id]["status"] = "completed"
            ACTIVE_DOWNLOADS[task_id]["progress"] = 100
            ACTIVE_DOWNLOADS[task_id]["message"] = f"Tous les titres sont prêts !"
            return

        cfg = load_config()
        music_base = cfg.get("music_folder", "Musique")
        audio_quality = cfg.get("audio_quality", "320")
        ffmpeg_path = get_ffmpeg_path()

        for idx, tr in enumerate(filtered_tracks, 1):
            title = tr.get("title", "")
            album = tr.get("album", "")
            cover_url = tr.get("thumbnail")

            ACTIVE_DOWNLOADS[task_id]["status"] = "downloading"
            ACTIVE_DOWNLOADS[task_id]["current_track"] = title
            ACTIVE_DOWNLOADS[task_id]["completed_tracks"] = completed
            ACTIVE_DOWNLOADS[task_id]["message"] = f"[{idx}/{total}] Téléchargement : {title}..."

            temp_dir = tempfile.mkdtemp(prefix="disco_")
            try:
                out_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
                ydl_opts = get_yt_dlp_common_opts()
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'outtmpl': out_template,
                    'noplaylist': True,
                })
                if ffmpeg_path:
                    ydl_opts['ffmpeg_location'] = ffmpeg_path
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': audio_quality,
                    }]
                    ydl_opts['postprocessor_args'] = {
                        'ffmpegextractaudio': ['-b:a', f'{audio_quality}k', '-ar', '44100']
                    }

                query = f"{artist_name} {title} lyrics"
                search_query = f"ytsearch1:{query}"
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(search_query, download=True)
                    entries = info.get('entries', []) if info else []
                    vid_info = entries[0] if entries else info

                downloaded_file = None
                for f in os.listdir(temp_dir):
                    if f.lower().endswith(".mp3"):
                        downloaded_file = os.path.join(temp_dir, f)
                        break

                if downloaded_file:
                    final_artist = sanitize_filename(artist_name)
                    final_title = sanitize_filename(title)
                    final_album = album if album else f"{final_artist} Singles"

                    tag_mp3(
                        file_path=downloaded_file,
                        artist=final_artist,
                        title=final_title,
                        album=final_album,
                        cover_url=cover_url or (vid_info.get('thumbnail') if vid_info else None)
                    )

                    dest_dir = os.path.join(music_base, final_artist)
                    os.makedirs(dest_dir, exist_ok=True)
                    target_path = os.path.join(dest_dir, f"{final_title}.mp3")

                    counter = 1
                    base_target = os.path.splitext(target_path)[0]
                    while os.path.exists(target_path):
                        target_path = f"{base_target} ({counter}).mp3"
                        counter += 1

                    shutil.move(downloaded_file, target_path)
                    completed += 1

                create_artist_files_and_playlist(artist_name, tracks)

            except Exception as e_batch:
                print(f"Erreur téléchargement morceau {title} : {e_batch}")
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

            pct = int((idx / total) * 100)
            ACTIVE_DOWNLOADS[task_id]["progress"] = pct
            ACTIVE_DOWNLOADS[task_id]["completed_tracks"] = completed

        ACTIVE_DOWNLOADS[task_id]["status"] = "completed"
        ACTIVE_DOWNLOADS[task_id]["progress"] = 100
        ACTIVE_DOWNLOADS[task_id]["message"] = f"Discographie terminée ! {completed} titres enregistrés dans le dossier {artist_name}."

    thread = threading.Thread(target=_batch_worker, daemon=True)
    thread.start()
    return task_id

def get_library():
    """Parcourt la bibliothèque musicale et organise les morceaux par chanteur (dossiers)."""
    cfg = load_config()
    music_base = cfg.get("music_folder", "Musique")

    if not os.path.exists(music_base):
        os.makedirs(music_base, exist_ok=True)
        return {"singers": [], "total_tracks": 0, "music_folder": music_base}

    singers_dict = {}
    total_tracks = 0

    for item in os.listdir(music_base):
        item_path = os.path.join(music_base, item)
        if os.path.isdir(item_path):
            singer_name = item
            tracks = []
            for f in os.listdir(item_path):
                if f.lower().endswith((".mp3", ".m4a", ".flac", ".ogg", ".wav")):
                    f_path = os.path.join(item_path, f)
                    meta = read_mp3_tags(f_path)
                    tracks.append({
                        "filename": f,
                        "rel_path": f"{singer_name}/{f}",
                        "title": meta.get("title") or os.path.splitext(f)[0],
                        "artist": meta.get("artist") or singer_name,
                        "album": meta.get("album", ""),
                        "duration": format_duration(meta.get("duration", 0)),
                        "duration_sec": meta.get("duration", 0),
                        "bitrate": meta.get("bitrate", 0),
                        "has_cover": meta.get("has_cover", False),
                        "size_mb": round(os.path.getsize(f_path) / (1024 * 1024), 2)
                    })
                    total_tracks += 1

            if tracks or os.path.isdir(item_path):
                singers_dict[singer_name] = tracks

        elif os.path.isfile(item_path) and item.lower().endswith((".mp3", ".m4a", ".flac", ".ogg", ".wav")):
            meta = read_mp3_tags(item_path)
            singer_name = meta.get("artist") or "Autres Morceaux"
            if singer_name not in singers_dict:
                singers_dict[singer_name] = []
            singers_dict[singer_name].append({
                "filename": item,
                "rel_path": item,
                "title": meta.get("title") or os.path.splitext(item)[0],
                "artist": singer_name,
                "album": meta.get("album", ""),
                "duration": format_duration(meta.get("duration", 0)),
                "duration_sec": meta.get("duration", 0),
                "bitrate": meta.get("bitrate", 0),
                "has_cover": meta.get("has_cover", False),
                "size_mb": round(os.path.getsize(item_path) / (1024 * 1024), 2)
            })
            total_tracks += 1

    singers_list = []
    for singer, tracks in sorted(singers_dict.items(), key=lambda x: x[0].lower()):
        singers_list.append({
            "singer": singer,
            "track_count": len(tracks),
            "tracks": sorted(tracks, key=lambda t: t["title"].lower())
        })

    return {
        "singers": singers_list,
        "total_tracks": total_tracks,
        "music_folder": music_base
    }

def delete_track(rel_path: str):
    """Supprime un morceau et son dossier de chanteur s'il est vide."""
    cfg = load_config()
    music_base = cfg.get("music_folder", "Musique")
    full_path = os.path.normpath(os.path.join(music_base, rel_path))

    if not full_path.startswith(os.path.normpath(music_base)):
        raise ValueError("Chemin interdit.")

    if os.path.exists(full_path):
        os.remove(full_path)
        parent_dir = os.path.dirname(full_path)
        if parent_dir != os.path.normpath(music_base) and os.path.exists(parent_dir):
            if not os.listdir(parent_dir):
                try:
                    os.rmdir(parent_dir)
                except Exception:
                    pass
        return True
    return False

def update_track_tags_and_move(rel_path: str, new_artist: str, new_title: str, new_album: str = None):
    """Met à jour les tags ID3 et déplace le fichier dans le bon dossier chanteur si nécessaire."""
    cfg = load_config()
    music_base = cfg.get("music_folder", "Musique")
    old_full_path = os.path.normpath(os.path.join(music_base, rel_path))

    if not os.path.exists(old_full_path):
        raise FileNotFoundError("Fichier introuvable.")

    clean_artist = sanitize_filename(new_artist) if new_artist else "Artiste Inconnu"
    clean_title = sanitize_filename(new_title) if new_title else "Sans Titre"

    tag_mp3(old_full_path, clean_artist, clean_title, new_album)

    new_dir = os.path.join(music_base, clean_artist)
    os.makedirs(new_dir, exist_ok=True)
    new_filename = f"{clean_title}.mp3"
    new_full_path = os.path.join(new_dir, new_filename)

    if old_full_path != new_full_path:
        shutil.move(old_full_path, new_full_path)
        old_parent = os.path.dirname(old_full_path)
        if old_parent != os.path.normpath(music_base) and os.path.exists(old_parent) and not os.listdir(old_parent):
            try:
                os.rmdir(old_parent)
            except Exception:
                pass

    return f"{clean_artist}/{new_filename}"


# =====================================================================
# FONCTIONS VIDÉO & STREAMING (MP4 HD & LECTURE EN LIGNE)
# =====================================================================

def search_videos(query: str, limit: int = 15):
    """
    Recherche des vidéos complètes (films, documentaires, clips, streaming)
    sur les plateformes vidéo gratuites (YouTube, Dailymotion, Vimeo, etc.).
    """
    results = []
    clean_q = query.strip()
    if not clean_q:
        return results

    # Si c'est un lien direct (YouTube, Dailymotion, Vimeo, etc.)
    if clean_q.startswith("http://") or clean_q.startswith("https://"):
        try:
            ydl_opts = get_yt_dlp_common_opts()
            ydl_opts['extract_flat'] = True
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(clean_q, download=False)
                if info:
                    vid_id = info.get('id', '')
                    title = info.get('title', 'Vidéo')
                    uploader = info.get('uploader') or info.get('channel', 'Web')
                    duration = info.get('duration', 0)
                    thumb = info.get('thumbnail')
                    if not thumb and info.get('thumbnails'):
                        thumb = info.get('thumbnails')[-1].get('url')
                    
                    embed_url = f"https://www.youtube-nocookie.com/embed/{vid_id}?autoplay=1&playsinline=1" if ("youtube" in clean_q or "youtu.be" in clean_q) else clean_q

                    return [{
                        "id": vid_id,
                        "title": title,
                        "url": clean_q,
                        "embed_url": embed_url,
                        "uploader": uploader,
                        "duration": format_duration(duration),
                        "duration_sec": duration,
                        "thumbnail": thumb or "/static/icons/icon-192.png",
                        "source": "Lien direct"
                    }]
        except Exception as e:
            print(f"Erreur extraction vidéo directe: {e}")

    # Recherche multi-vidéo
    try:
        ydl_opts = get_yt_dlp_common_opts()
        ydl_opts['extract_flat'] = True
        ydl_opts['noplaylist'] = True

        yt_query = f"ytsearch{limit}:{clean_q}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(yt_query, download=False)
            entries = res.get('entries', []) if res else []
            for entry in entries:
                if not entry:
                    continue
                vid_id = entry.get('id')
                title = entry.get('title', 'Vidéo')
                uploader = entry.get('uploader') or entry.get('channel', 'Chaîne')
                dur = entry.get('duration', 0)
                thumb = entry.get('thumbnail')
                if not thumb and entry.get('thumbnails'):
                    thumb = entry.get('thumbnails')[-1].get('url')
                if not thumb and vid_id:
                    thumb = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                
                web_url = entry.get('url') or entry.get('webpage_url') or f"https://www.youtube.com/watch?v={vid_id}"
                embed_url = f"https://www.youtube-nocookie.com/embed/{vid_id}?autoplay=1&playsinline=1"

                results.append({
                    "id": vid_id,
                    "title": title,
                    "url": web_url,
                    "embed_url": embed_url,
                    "uploader": uploader,
                    "duration": format_duration(dur),
                    "duration_sec": dur,
                    "thumbnail": thumb or "/static/icons/icon-192.png",
                    "source": "Gratuit / Streaming"
                })
    except Exception as e:
        print(f"Erreur recherche vidéo: {e}")

    return results

def download_video_async(url: str, title: str = "", task_id: str = None):
    """
    Télécharge une vidéo complète en fichier MP4 HD (1080p/720p).
    Garantit la compatibilité mobile et PC.
    """
    if not task_id:
        task_id = str(uuid.uuid4())

    ACTIVE_DOWNLOADS[task_id] = {
        "id": task_id,
        "type": "video",
        "status": "starting",
        "progress": 0,
        "title": title or "Vidéo",
        "message": "Démarrage du téléchargement vidéo MP4...",
        "filepath": None,
        "filename": None,
        "error": None
    }

    def _video_worker():
        try:
            ACTIVE_DOWNLOADS[task_id]["status"] = "downloading"
            cfg = load_config()
            music_base = cfg.get("music_folder", "Musique")
            video_dir = os.path.join(music_base, "Videos")
            os.makedirs(video_dir, exist_ok=True)
            ffmpeg_path = get_ffmpeg_path()

            def hook_cb(d):
                if d.get('status') == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    downloaded = d.get('downloaded_bytes') or 0
                    if total > 0:
                        pct = int((downloaded / total) * 90)
                        ACTIVE_DOWNLOADS[task_id]["progress"] = max(5, min(pct, 90))
                        ACTIVE_DOWNLOADS[task_id]["message"] = f"Téléchargement vidéo : {pct}%"
                elif d.get('status') == 'finished':
                    ACTIVE_DOWNLOADS[task_id]["progress"] = 95
                    ACTIVE_DOWNLOADS[task_id]["message"] = "Finalisation du fichier vidéo MP4..."

            out_template = os.path.join(video_dir, "%(title)s.%(ext)s")
            ydl_opts = get_yt_dlp_common_opts()
            ydl_opts.update({
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': out_template,
                'progress_hooks': [hook_cb],
                'noplaylist': True,
                'merge_output_format': 'mp4'
            })
            if ffmpeg_path:
                ydl_opts['ffmpeg_location'] = ffmpeg_path

            effective_url = url
            if not (url.startswith("http://") or url.startswith("https://")):
                effective_url = f"ytsearch1:{url}"
            elif any(domain in url for domain in ["imdb.com", "multiembed", "vidsrc", "2embed", "autoembed", "superembed"]):
                clean_title = re.sub(r'https?://[^\s]+', '', title or '').strip()
                effective_url = f"ytsearch1:{clean_title} film complet francais"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(effective_url, download=True)
                if 'entries' in info and info['entries']:
                    info = info['entries'][0]

            target_file = None
            if info:
                expected_filename = ydl.prepare_filename(info)
                base, _ = os.path.splitext(expected_filename)
                mp4_filename = base + ".mp4"
                if os.path.exists(mp4_filename):
                    target_file = mp4_filename
                elif os.path.exists(expected_filename):
                    target_file = expected_filename

            if not target_file:
                files = [os.path.join(video_dir, f) for f in os.listdir(video_dir) if f.lower().endswith(('.mp4', '.mkv', '.webm'))]
                if files:
                    target_file = max(files, key=os.path.getmtime)

            if not target_file or not os.path.exists(target_file):
                raise Exception("Le fichier vidéo n'a pas pu être enregistré.")

            final_name = os.path.basename(target_file)
            ACTIVE_DOWNLOADS[task_id]["status"] = "completed"
            ACTIVE_DOWNLOADS[task_id]["progress"] = 100
            ACTIVE_DOWNLOADS[task_id]["message"] = "✅ Vidéo MP4 prête à être téléchargée !"
            ACTIVE_DOWNLOADS[task_id]["filepath"] = target_file
            ACTIVE_DOWNLOADS[task_id]["filename"] = final_name
            ACTIVE_DOWNLOADS[task_id]["title"] = os.path.splitext(final_name)[0]
        except Exception as e:
            print(f"Erreur téléchargement vidéo: {e}")
            ACTIVE_DOWNLOADS[task_id]["status"] = "error"
            ACTIVE_DOWNLOADS[task_id]["error"] = str(e)
            ACTIVE_DOWNLOADS[task_id]["message"] = f"Erreur : {str(e)[:120]}"

    thread = threading.Thread(target=_video_worker, daemon=True)
    thread.start()
    return task_id
