import os
import sys
import time
import shutil
import tempfile
import threading
import uuid
import yt_dlp
import imageio_ffmpeg
import requests

from config import load_config
from music_tagger import (
    sanitize_filename,
    clean_noise_from_title,
    clean_artist_name,
    parse_artist_and_title,
    tag_mp3,
    read_mp3_tags
)

# Suivi des téléchargements actifs pour l'interface en temps réel
ACTIVE_DOWNLOADS = {}

def get_ffmpeg_path():
    """Récupère le chemin exécutable de ffmpeg fourni par imageio-ffmpeg."""
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as e:
        print(f"Avertissement ffmpeg : {e}")
        return None

def format_duration(seconds):
    """Formate les secondes en MM:SS."""
    if not seconds:
        return "00:00"
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"

def pick_best_studio_track(entries, expected_artist="", expected_title=""):
    """
    Sélectionne la piste audio studio officielle et propre :
    Évite les clips avec dialogue d'intro/outro, parodies, interviews, réact, live.
    Privilégie les chaînes officielles 'Topic', 'Official Audio', et les versions studio pures.
    """
    if not entries:
        return None
        
    def calculate_score(entry):
        title = (entry.get('title') or '').lower()
        uploader = (entry.get('uploader') or '').lower()
        duration = entry.get('duration') or 0
        score = 50
        
        # 1. Éliminer formellement les bruits indésirables / vidéos parasites
        bad_words = [
            'interview', 'parodie', 'parody', 'reaction', 'react', 'court métrage',
            'court-métrage', 'short film', 'behind the scenes', 'making of', 'teaser',
            'trailer', 'vlog', 'live', 'concert', 'acoustic', 'unplugged', 'karaoke',
            'remix', 'bass boosted', 'nightcore', 'sped up', 'slowed', 'instrumental'
        ]
        for w in bad_words:
            if w in title:
                score -= 60

        # Si le clip vidéo officiel a souvent des dialogues ajoutés au début ou à la fin
        if 'clip officiel' in title or 'official video' in title or 'vidéo officielle' in title:
            score -= 20

        # 2. PRIORITÉ ABSOLUE : PISTES LYRICS / PAROLES (Bande-son studio pure sans dialogue)
        if 'lyrics' in title or 'lyric' in title or 'paroles' in title:
            score += 90
        if 'lyric video' in title or 'official lyric' in title:
            score += 40
            
        # 3. Privilégier également les sources audio studio officielles (Topic / Official Audio)
        if ' - topic' in uploader or 'topic' in uploader:
            score += 45
        if 'official audio' in title or 'audio officiel' in title or '(audio)' in title or '[audio]' in title:
            score += 35
        if 'provided to youtube' in (entry.get('description') or '').lower():
            score += 40

        # 4. Correspondance de nom d'artiste dans l'uploader
        if expected_artist and expected_artist.lower() in uploader:
            score += 20
            
        # 5. Longueur normale pour une chanson (entre 1m30 et 6m30)
        if 90 <= duration <= 390:
            score += 15
        elif duration < 60 or duration > 600:
            score -= 30
            
        return score

    sorted_entries = sorted(entries, key=calculate_score, reverse=True)
    return sorted_entries[0]

def search_tracks(query: str, limit: int = 10):
    """
    Recherche des morceaux en utilisant yt-dlp et l'API iTunes pour des métadonnées précises.
    Permet à l'utilisateur de trouver la musique, avec détection automatique du chanteur et du titre.
    """
    cfg = load_config()
    results = []

    # Si l'utilisateur colle directement une URL
    if query.startswith("http://") or query.startswith("https://"):
        try:
            ydl_opts = {
                'quiet': True,
                'extract_flat': True,
                'noplaylist': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                if info:
                    raw_title = info.get('title', 'Musique')
                    uploader = info.get('uploader') or info.get('channel', '')
                    artist_meta = info.get('artist')
                    track_meta = info.get('track')

                    artist, title = parse_artist_and_title(raw_title, uploader, artist_meta, track_meta)

                    return [{
                        "id": info.get('id', str(uuid.uuid4())),
                        "url": query,
                        "raw_title": raw_title,
                        "title": title,
                        "artist": artist,
                        "uploader": uploader,
                        "duration": format_duration(info.get('duration', 0)),
                        "duration_sec": info.get('duration', 0),
                        "thumbnail": info.get('thumbnail', ''),
                        "source": "Lien Direct / " + (info.get('extractor_key') or "Web")
                    }]
        except Exception as e:
            print(f"Erreur extraction URL directe : {e}")

    # Recherche standard via ytsearch
    try:
        # Priorité absolue demandée : rechercher les versions LYRICS (musique studio propre sans dialogue)
        search_engine = "ytsearch"
        clean_q = query
        if not clean_q.startswith("http") and "lyric" not in clean_q.lower() and "parole" not in clean_q.lower():
            search_query = f"{search_engine}{limit}:{clean_q} lyrics"
        else:
            search_query = f"{search_engine}{limit}:{clean_q}"
        
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(search_query, download=False)
            entries = res.get('entries', []) if res else []

            for entry in entries:
                if not entry:
                    continue
                raw_title = entry.get('title', '')
                uploader = entry.get('uploader') or entry.get('channel', '')
                artist_meta = entry.get('artist')
                track_meta = entry.get('track')

                artist, title = parse_artist_and_title(raw_title, uploader, artist_meta, track_meta)

                # Thumbnail
                thumb = entry.get('thumbnail', '')
                if not thumb and entry.get('thumbnails'):
                    thumb = entry.get('thumbnails')[-1].get('url', '')

                url = entry.get('url') or entry.get('webpage_url')
                if not url and entry.get('id'):
                    url = f"https://www.youtube.com/watch?v={entry.get('id')}"

                results.append({
                    "id": entry.get('id', str(uuid.uuid4())),
                    "url": url,
                    "raw_title": raw_title,
                    "title": title,
                    "artist": artist,
                    "uploader": uploader,
                    "duration": format_duration(entry.get('duration', 0)),
                    "duration_sec": entry.get('duration', 0),
                    "thumbnail": thumb,
                    "source": "Recherche Music"
                })

    except Exception as e:
        print(f"Erreur recherche yt-dlp : {e}")

    return results

def download_track_async(url: str, chosen_artist: str, chosen_title: str, album: str = None, cover_url: str = None, task_id: str = None):
    """
    Télécharge le morceau en MP3 en tâche de fond.
    1. Télécharge et extrait l'audio en MP3
    2. Crée le dossier par chanteur (si configuré)
    3. Tagge le fichier avec les métadonnées ID3 (Chanteur, Titre, Album, Pochette)
    """
    if not task_id:
        task_id = str(uuid.uuid4())

    ACTIVE_DOWNLOADS[task_id] = {
        "id": task_id,
        "status": "starting",
        "progress": 0,
        "artist": chosen_artist,
        "title": chosen_title,
        "message": "Démarrage du téléchargement...",
        "filepath": None,
        "error": None
    }

    def _worker():
        temp_dir = tempfile.mkdtemp(prefix="mp3_down_")
        try:
            cfg = load_config()
            music_base = cfg.get("music_folder", "Musique")
            create_folder_per_artist = cfg.get("create_artist_folder", True)
            audio_quality = cfg.get("audio_quality", "320")

            ffmpeg_path = get_ffmpeg_path()

            ACTIVE_DOWNLOADS[task_id]["status"] = "downloading"
            ACTIVE_DOWNLOADS[task_id]["message"] = "Téléchargement du flux audio HD..."

            def progress_hook(d):
                if d.get('status') == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    downloaded = d.get('downloaded_bytes') or 0
                    if total > 0:
                        pct = int((downloaded / total) * 80)
                        ACTIVE_DOWNLOADS[task_id]["progress"] = min(pct, 80)
                        ACTIVE_DOWNLOADS[task_id]["message"] = f"Téléchargement : {pct}%"
                elif d.get('status') == 'finished':
                    ACTIVE_DOWNLOADS[task_id]["progress"] = 85
                    ACTIVE_DOWNLOADS[task_id]["status"] = "converting"
                    ACTIVE_DOWNLOADS[task_id]["message"] = "Encodage MP3 HD (320 kbps)..."

            out_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': out_template,
                'progress_hooks': [progress_hook],
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
            }

            if ffmpeg_path:
                ydl_opts['ffmpeg_location'] = ffmpeg_path
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': audio_quality,
                }]
                # Forcer le débit exact via postprocessor_args (format dict yt-dlp moderne)
                ydl_opts['postprocessor_args'] = {
                    'ffmpegextractaudio': ['-b:a', f'{audio_quality}k', '-ar', '44100']
                }

            # Si l'URL fournie est une recherche, chercher les versions LYRICS studio propres
            effective_url = url
            if not (url.startswith("http://") or url.startswith("https://")):
                clean_search = f"ytsearch6:{url} lyrics"
                with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True, 'noplaylist': True}) as ydl_search:
                    res = ydl_search.extract_info(clean_search, download=False)
                    cand_entries = res.get('entries', []) if res else []
                    best = pick_best_studio_track(cand_entries, chosen_artist, chosen_title)
                    if best:
                        effective_url = best.get('url') or best.get('webpage_url') or f"https://www.youtube.com/watch?v={best.get('id')}"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(effective_url, download=True)

            # Trouver le fichier MP3 téléchargé dans le dossier temporaire
            downloaded_mp3 = None
            for f in os.listdir(temp_dir):
                if f.lower().endswith(".mp3"):
                    downloaded_mp3 = os.path.join(temp_dir, f)
                    break

            if not downloaded_mp3:
                # Si le fichier n'a pas été converti en .mp3 (par ex si ffmpeg a échoué), chercher n'importe quel fichier audio
                files = os.listdir(temp_dir)
                if files:
                    downloaded_mp3 = os.path.join(temp_dir, files[0])
                else:
                    raise Exception("Aucun fichier audio extrait.")

            ACTIVE_DOWNLOADS[task_id]["status"] = "tagging"
            ACTIVE_DOWNLOADS[task_id]["progress"] = 90
            ACTIVE_DOWNLOADS[task_id]["message"] = "Organisation et marquage du chanteur (ID3)..."

            # Récupération de la pochette si non fournie
            effective_cover = cover_url
            if not effective_cover and info:
                effective_cover = info.get('thumbnail')

            # Nettoyage et préparation du nom du chanteur et titre
            final_artist = sanitize_filename(chosen_artist) if chosen_artist else "Artiste Inconnu"
            final_title = sanitize_filename(chosen_title) if chosen_title else "Sans Titre"
            final_album = album if album else f"{final_artist} Singles"

            # 1. Écriture des métadonnées ID3 dans le fichier MP3
            tag_mp3(
                file_path=downloaded_mp3,
                artist=final_artist,
                title=final_title,
                album=final_album,
                cover_url=effective_cover
            )

            # 2. Création du dossier par chanteur (ex: Musique/Céline Dion/)
            if create_folder_per_artist:
                dest_dir = os.path.join(music_base, final_artist)
            else:
                dest_dir = music_base

            os.makedirs(dest_dir, exist_ok=True)

            # 3. Déplacement du fichier MP3 dans le dossier final
            target_filename = f"{final_title}.mp3"
            target_path = os.path.join(dest_dir, target_filename)

            # Éviter l'écrasement en cas de doublon
            counter = 1
            base_target = os.path.splitext(target_path)[0]
            while os.path.exists(target_path):
                target_path = f"{base_target} ({counter}).mp3"
                counter += 1

            shutil.move(downloaded_mp3, target_path)

            ACTIVE_DOWNLOADS[task_id]["status"] = "completed"
            ACTIVE_DOWNLOADS[task_id]["progress"] = 100
            ACTIVE_DOWNLOADS[task_id]["message"] = f"Téléchargement terminé ! Sauvegardé dans {final_artist}"
            ACTIVE_DOWNLOADS[task_id]["filepath"] = target_path
            ACTIVE_DOWNLOADS[task_id]["filename"] = os.path.basename(target_path)
            ACTIVE_DOWNLOADS[task_id]["artist"] = final_artist
            ACTIVE_DOWNLOADS[task_id]["title"] = final_title

        except Exception as e:
            print(f"Erreur téléchargement tâche {task_id} : {e}")
            ACTIVE_DOWNLOADS[task_id]["status"] = "error"
            ACTIVE_DOWNLOADS[task_id]["error"] = str(e)
            ACTIVE_DOWNLOADS[task_id]["message"] = f"Erreur : {e}"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return task_id

def get_library():
    """
    Parcourt la bibliothèque musicale et organise les morceaux par chanteur (dossiers).
    Renvoie la liste des chanteurs et leurs musiques respectives.
    """
    cfg = load_config()
    music_base = cfg.get("music_folder", "Musique")

    if not os.path.exists(music_base):
        os.makedirs(music_base, exist_ok=True)
        return {"singers": [], "total_tracks": 0, "music_folder": music_base}

    singers_dict = {}
    total_tracks = 0

    # 1. Parcourir les dossiers de chanteurs
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
            # Morceau à la racine
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

    # Convertir en liste ordonnée
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

    # Sécurité : vérifier que le fichier reste dans le dossier musique
    if not full_path.startswith(os.path.normpath(music_base)):
        raise ValueError("Chemin interdit.")

    if os.path.exists(full_path):
        os.remove(full_path)
        # Supprimer le dossier du chanteur s'il est vide
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

    # 1. Mettre à jour les tags ID3
    tag_mp3(old_full_path, clean_artist, clean_title, new_album)

    # 2. Déplacer vers le nouveau dossier chanteur si nécessaire
    new_dir = os.path.join(music_base, clean_artist)
    os.makedirs(new_dir, exist_ok=True)
    new_filename = f"{clean_title}.mp3"
    new_full_path = os.path.join(new_dir, new_filename)

    if old_full_path != new_full_path:
        shutil.move(old_full_path, new_full_path)
        # Supprimer l'ancien dossier s'il est vide
        old_parent = os.path.dirname(old_full_path)
        if old_parent != os.path.normpath(music_base) and os.path.exists(old_parent) and not os.listdir(old_parent):
            try:
                os.rmdir(old_parent)
            except Exception:
                pass

    return f"{clean_artist}/{new_filename}"

def download_singer_discography_async(artist_name: str, tracks: list, skip_duplicates: bool = True, task_id: str = None):
    """
    Télécharge la discographie complète d'un chanteur ou d'une chanteuse en tâche de fond.
    1. Filtre et saute automatiquement les morceaux déjà présents sur l'ordinateur ou le téléphone
    2. Télécharge chaque morceau en haute qualité MP3
    3. Met à jour les tags ID3 officiels (Chanteur, Titre, Album, Pochette)
    4. Crée le dossier du chanteur et met à jour la playlist .m3u8 et le fichier discographie.json
    """
    if not task_id:
        task_id = str(uuid.uuid4())

    # Filtrer les morceaux à télécharger
    filtered_tracks = []
    skipped_count = 0
    for t in tracks:
        if skip_duplicates and t.get("is_duplicate"):
            skipped_count += 1
        else:
            filtered_tracks.append(t)

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
        "message": f"Démarrage : {len(filtered_tracks)} titres à télécharger ({skipped_count} doublons évités)...",
        "error": None
    }

    def _batch_worker():
        from scanner import create_artist_files_and_playlist
        total = len(filtered_tracks)
        completed = 0

        # Créer les fichiers récapitulatifs pour l'artiste dès le départ
        create_artist_files_and_playlist(artist_name, tracks)

        if total == 0:
            ACTIVE_DOWNLOADS[task_id]["status"] = "completed"
            ACTIVE_DOWNLOADS[task_id]["progress"] = 100
            ACTIVE_DOWNLOADS[task_id]["message"] = f"Tous les titres de {artist_name} sont déjà présents sur votre appareil ! (0 doublon téléchargé)"
            return

        for idx, tr in enumerate(filtered_tracks, 1):
            title = tr.get("title", "")
            album = tr.get("album", "")
            cover_url = tr.get("thumbnail")

            ACTIVE_DOWNLOADS[task_id]["status"] = "downloading"
            ACTIVE_DOWNLOADS[task_id]["current_track"] = title
            ACTIVE_DOWNLOADS[task_id]["completed_tracks"] = completed
            ACTIVE_DOWNLOADS[task_id]["message"] = f"[{idx}/{total}] Téléchargement : {title}..."

            # Rechercher la piste LYRICS originale propre sans intro/dialogue de clip
            query = f"{artist_name} {title} lyrics"
            search_query = f"ytsearch6:{query}"

            temp_dir = tempfile.mkdtemp(prefix="disco_")
            try:
                cfg = load_config()
                music_base = cfg.get("music_folder", "Musique")
                audio_quality = cfg.get("audio_quality", "320")
                ffmpeg_path = get_ffmpeg_path()

                # Recherche préalable pour sélectionner la piste officielle la plus pure
                search_opts = {'quiet': True, 'extract_flat': True, 'noplaylist': True}
                with yt_dlp.YoutubeDL(search_opts) as ydl_s:
                    s_res = ydl_s.extract_info(search_query, download=False)
                    cand_entries = s_res.get('entries', []) if s_res else []
                    best_cand = pick_best_studio_track(cand_entries, artist_name, title)

                target_download_url = search_query
                if best_cand:
                    target_download_url = best_cand.get('url') or best_cand.get('webpage_url') or f"https://www.youtube.com/watch?v={best_cand.get('id')}"

                out_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': out_template,
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True,
                }
                if ffmpeg_path:
                    ydl_opts['ffmpeg_location'] = ffmpeg_path
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': audio_quality,
                    }]
                    # Forcer le débit exact via postprocessor_args (format dict yt-dlp moderne)
                    ydl_opts['postprocessor_args'] = {
                        'ffmpegextractaudio': ['-b:a', f'{audio_quality}k', '-ar', '44100']
                    }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(target_download_url, download=True)
                    entries = info.get('entries', []) if info else []
                    vid_info = entries[0] if entries else info

                # Trouver le fichier MP3 téléchargé
                downloaded_file = None
                for f in os.listdir(temp_dir):
                    if f.lower().endswith(".mp3"):
                        downloaded_file = os.path.join(temp_dir, f)
                        break

                if downloaded_file:
                    final_artist = sanitize_filename(artist_name)
                    final_title = sanitize_filename(title)
                    final_album = album if album else f"{final_artist} Singles"

                    # 1. Écriture des tags ID3
                    tag_mp3(
                        file_path=downloaded_file,
                        artist=final_artist,
                        title=final_title,
                        album=final_album,
                        cover_url=cover_url or (vid_info.get('thumbnail') if vid_info else None)
                    )

                    # 2. Dossier par chanteur
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

                # Mettre à jour la playlist et fichiers du chanteur à chaque téléchargement
                create_artist_files_and_playlist(artist_name, tracks)

            except Exception as e:
                print(f"Erreur téléchargement morceau {title}: {e}")
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

            # Calcul du progrès
            pct = int((idx / total) * 100)
            ACTIVE_DOWNLOADS[task_id]["progress"] = pct
            ACTIVE_DOWNLOADS[task_id]["completed_tracks"] = completed

        ACTIVE_DOWNLOADS[task_id]["status"] = "completed"
        ACTIVE_DOWNLOADS[task_id]["progress"] = 100
        ACTIVE_DOWNLOADS[task_id]["message"] = f"Discographie terminée ! {completed} titres enregistrés dans le dossier {artist_name} ({skipped_count} doublons évités)."

    thread = threading.Thread(target=_batch_worker, daemon=True)
    thread.start()
    return task_id
