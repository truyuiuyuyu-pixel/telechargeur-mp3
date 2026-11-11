import os
import re
import json
import unicodedata
import requests
from config import load_config
from music_tagger import sanitize_filename, read_mp3_tags

def normalize_string(text: str) -> str:
    """Normalise une chaîne pour comparaison insensible aux accents, casse, ponctuation et parenthèses."""
    if not text:
        return ""
    # Retirer les accents (é -> e, ç -> c, etc.)
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    text = text.lower()
    # Retirer le contenu entre parenthèses ou crochets : (Clip officiel), [HD], etc.
    text = re.sub(r'[\(\[\{][^\)\]\}]*[\)\]\}]', '', text)
    # Retirer les mots parasites fréquents
    noise = [
        'feat', 'ft', 'featuring', 'remastered', 'remaster', 'live', 
        'version', 'clip', 'officiel', 'official', 'audio', 'video', 
        'paroles', 'lyrics', 'original'
    ]
    pattern = r'\b(?:' + '|'.join(noise) + r')\b.*'
    text = re.sub(pattern, '', text)
    # Ne garder que lettres et chiffres
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

def is_duplicate_title(title1: str, title2: str) -> bool:
    """Compare deux titres de manière intelligente pour détecter un doublon."""
    norm1 = normalize_string(title1)
    norm2 = normalize_string(title2)
    if not norm1 or not norm2:
        return False
    if norm1 == norm2:
        return True
    # Si l'un est inclus dans l'autre (ex: "pour que tu maimes encore" dans "celine dion pour que tu maimes encore")
    if len(norm1) >= 6 and len(norm2) >= 6:
        if norm1 in norm2 or norm2 in norm1:
            return True
    return False

def scan_all_existing_music():
    r"""
    Scanne l'ordinateur pour trouver tous les fichiers musicaux existants :
    1. Le dossier de l'application (ex: e:\app télécharger\Musique)
    2. Le dossier Musique de l'utilisateur Windows (ex: C:\Users\<user>\Music)
    3. Les fichiers enregistrés comme étant sur le téléphone
    Renvoie une liste indexée de morceaux existants pour le filtrage anti-doublon.
    """
    cfg = load_config()
    scan_paths = []

    # 1. Dossier de l'app
    app_music = cfg.get("music_folder", "Musique")
    if os.path.exists(app_music):
        scan_paths.append(("App Musique", app_music))

    # 2. Dossier Musique Windows
    try:
        user_music = os.path.join(os.path.expanduser("~"), "Music")
        if os.path.exists(user_music) and os.path.normpath(user_music) != os.path.normpath(app_music):
            scan_paths.append(("PC Musique Windows", user_music))
    except Exception:
        pass

    existing_tracks = []
    
    for source_label, root_dir in scan_paths:
        try:
            for root, dirs, files in os.walk(root_dir):
                for f in files:
                    if f.lower().endswith(('.mp3', '.m4a', '.flac', '.ogg', '.wav')):
                        full_p = os.path.join(root, f)
                        meta = read_mp3_tags(full_p)
                        title = meta.get("title") or os.path.splitext(f)[0]
                        artist = meta.get("artist") or os.path.basename(root)
                        
                        existing_tracks.append({
                            "source": source_label,
                            "filename": f,
                            "path": full_p,
                            "title": title,
                            "artist": artist,
                            "norm_title": normalize_string(title),
                            "norm_artist": normalize_string(artist),
                            "size_bytes": os.path.getsize(full_p) if os.path.exists(full_p) else 0
                        })
        except Exception as e:
            print(f"Erreur scan {root_dir}: {e}")

    # Charger également l'index des fichiers déclarés sur le téléphone (s'il existe)
    phone_index_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phone_music_index.json')
    if os.path.exists(phone_index_file):
        try:
            with open(phone_index_file, 'r', encoding='utf-8') as f:
                phone_tracks = json.load(f)
                for pt in phone_tracks:
                    existing_tracks.append({
                        "source": "Téléphone (Mobile)",
                        "filename": pt.get("filename", ""),
                        "path": "Téléphone",
                        "title": pt.get("title", ""),
                        "artist": pt.get("artist", ""),
                        "norm_title": normalize_string(pt.get("title", "")),
                        "norm_artist": normalize_string(pt.get("artist", "")),
                        "size_bytes": 0
                    })
        except Exception:
            pass

    return existing_tracks

def search_singer_discography(artist_name: str, limit: int = 50):
    """
    Recherche la discographie complète / les titres populaires d'un chanteur ou d'une chanteuse.
    Scanne les appareils (PC & Téléphone) pour identifier immédiatement les doublons.
    """
    artist_clean = artist_name.strip()
    if not artist_clean:
        return {"artist": "", "tracks": [], "existing_count": 0, "new_count": 0}

    # 1. Récupération des titres via iTunes Search API (officiel, propre, avec pochettes HD et albums)
    tracks_found = []
    seen_norm_titles = set()

    try:
        url = "https://itunes.apple.com/search"
        params = {
            "term": artist_clean,
            "entity": "song",
            "attribute": "artistTerm",
            "limit": limit
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("results", []):
                t_name = item.get("trackName", "")
                a_name = item.get("artistName", artist_clean)
                album_name = item.get("collectionName", "")
                norm_t = normalize_string(t_name)
                
                # Éviter les doublons au sein des résultats iTunes (ex: versions différentes sur 3 compilations)
                if norm_t in seen_norm_titles:
                    continue
                seen_norm_titles.add(norm_t)

                # Pochette haute résolution (600x600)
                art_url = item.get("artworkUrl100", "")
                if art_url:
                    art_url = art_url.replace("100x100bb.jpg", "600x600bb.jpg")

                duration_ms = item.get("trackTimeMillis", 0)
                duration_sec = int(duration_ms / 1000)
                m = duration_sec // 60
                s = duration_sec % 60
                duration_str = f"{m:02d}:{s:02d}"

                tracks_found.append({
                    "title": t_name,
                    "artist": a_name,
                    "album": album_name,
                    "release_year": item.get("releaseDate", "")[:4],
                    "duration": duration_str,
                    "duration_sec": duration_sec,
                    "thumbnail": art_url,
                    "preview_url": item.get("previewUrl", "")
                })
    except Exception as e:
        print(f"Erreur recherche discographie iTunes : {e}")

    # Fallback Deezer si iTunes retourne peu de résultats
    if len(tracks_found) < 5:
        try:
            d_url = f"https://api.deezer.com/search?q=artist:\"{artist_clean}\"&limit={limit}"
            d_resp = requests.get(d_url, timeout=10)
            if d_resp.status_code == 200:
                d_data = d_resp.json()
                for item in d_data.get("data", []):
                    t_name = item.get("title_short") or item.get("title", "")
                    a_name = item.get("artist", {}).get("name", artist_clean)
                    album_name = item.get("album", {}).get("title", "")
                    norm_t = normalize_string(t_name)
                    
                    if norm_t in seen_norm_titles:
                        continue
                    seen_norm_titles.add(norm_t)

                    duration_sec = item.get("duration", 0)
                    m = duration_sec // 60
                    s = duration_sec % 60
                    duration_str = f"{m:02d}:{s:02d}"

                    tracks_found.append({
                        "title": t_name,
                        "artist": a_name,
                        "album": album_name,
                        "release_year": "",
                        "duration": duration_str,
                        "duration_sec": duration_sec,
                        "thumbnail": item.get("album", {}).get("cover_big", ""),
                        "preview_url": item.get("preview", "")
                    })
        except Exception as e:
            print(f"Erreur recherche discographie Deezer : {e}")

    # 2. Scanner tous les fichiers existants sur PC et Téléphone pour DÉTECTER LES DOUBLONS
    existing_music = scan_all_existing_music()
    norm_artist_target = normalize_string(artist_clean)

    discography_tracks = []
    existing_count = 0
    new_count = 0

    for tr in tracks_found:
        norm_t = normalize_string(tr["title"])
        is_dup = False
        dup_info = None

        for ext in existing_music:
            # Vérifie si le titre correspond
            if is_duplicate_title(tr["title"], ext["title"]) or is_duplicate_title(tr["title"], ext["filename"]):
                # Si le chanteur correspond aussi ou si l'artiste est dans le titre
                if (norm_artist_target in ext["norm_artist"] or ext["norm_artist"] in norm_artist_target or 
                    norm_artist_target in ext["norm_title"]):
                    is_dup = True
                    dup_info = {
                        "source": ext["source"],
                        "path": ext["path"],
                        "filename": ext["filename"]
                    }
                    break

        # Vérification d'appartenance au chanteur choisi
        norm_item_a = normalize_string(tr.get("artist", ""))
        is_verified_artist = (norm_artist_target in norm_item_a or norm_item_a in norm_artist_target)
        # Vérifier aussi qu'il ne s'agit pas d'une reprise
        title_low = tr.get("title", "").lower()
        if any(w in title_low for w in ['cover', 'reprise', 'tribute', 'karaoke', 'parodie', 'in the style of']):
            is_verified_artist = False

        item_result = {
            **tr,
            "is_duplicate": is_dup,
            "duplicate_info": dup_info,
            "belongs_to_artist": is_verified_artist,
            "verification_badge": "✅ Chanteur Officiel" if is_verified_artist else "⚠️ Interprète Différent",
            "status": "already_present" if is_dup else "to_download"
        }

        if is_dup:
            existing_count += 1
        else:
            new_count += 1

        discography_tracks.append(item_result)

    return {
        "artist": artist_clean,
        "tracks": discography_tracks,
        "total_tracks": len(discography_tracks),
        "existing_count": existing_count,
        "new_count": new_count
    }

def create_artist_files_and_playlist(artist_name: str, tracks: list):
    """
    Crée les fichiers dédiés pour le/la chanteur/chanteuse :
    1. Le dossier du chanteur : Musique/<Nom_du_Chanteur>/
    2. Le fichier d'index et métadonnées : Musique/<Nom_du_Chanteur>/discographie.json
    3. La playlist universelle .m3u8 reconnue par les lecteurs du téléphone et de l'ordinateur
    4. Le fichier texte lisible : Musique/<Nom_du_Chanteur>/liste_des_titres.txt
    """
    cfg = load_config()
    music_base = cfg.get("music_folder", "Musique")
    clean_artist = sanitize_filename(artist_name)
    artist_dir = os.path.join(music_base, clean_artist)
    os.makedirs(artist_dir, exist_ok=True)

    # 1. Fichier de discographie JSON
    discography_file = os.path.join(artist_dir, "discographie.json")
    summary_data = {
        "artist": clean_artist,
        "total_tracks": len(tracks),
        "tracks": tracks
    }
    with open(discography_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=4, ensure_ascii=False)

    # 2. Fichier texte récapitulatif
    txt_file = os.path.join(artist_dir, "liste_des_titres.txt")
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(f"=== DISCOGRAPHIE : {clean_artist.upper()} ===\n")
        f.write(f"Nombre de morceaux référencés : {len(tracks)}\n\n")
        for i, t in enumerate(tracks, 1):
            status = " [DÉJÀ PRÉSENT]" if t.get("is_duplicate") else " [À TÉLÉCHARGER]"
            f.write(f"{i:02d}. {t.get('title')} - {t.get('album', '')} ({t.get('duration', '')}){status}\n")

    # 3. Fichier Playlist M3U8 pour téléphone et ordinateur
    # Ce fichier est compatible avec tous les lecteurs (Samsung Music, Apple Music, VLC, Windows Media, etc.)
    m3u_file = os.path.join(artist_dir, f"{clean_artist} - Playlist.m3u8")
    with open(m3u_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"#PLAYLIST:{clean_artist}\n\n")
        # Répertorier tous les fichiers MP3 existants dans ce dossier
        for f_name in sorted(os.listdir(artist_dir)):
            if f_name.lower().endswith(".mp3"):
                f.write(f"#EXTINF:-1,{clean_artist} - {os.path.splitext(f_name)[0]}\n")
                f.write(f"{f_name}\n")

    return {
        "artist_dir": artist_dir,
        "discography_file": discography_file,
        "playlist_file": m3u_file,
        "txt_file": txt_file
    }

def register_phone_music(file_list: list):
    """
    Permet à l'application mobile (téléphone) de déclarer les musiques présentes sur le smartphone
    pour que le scanner anti-doublon les prenne en compte immédiatement.
    """
    phone_index_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phone_music_index.json')
    try:
        current = []
        if os.path.exists(phone_index_file):
            with open(phone_index_file, 'r', encoding='utf-8') as f:
                current = json.load(f)
        
        # Ajouter les nouveaux morceaux sans écraser les anciens
        existing_names = {x.get("filename", "").lower() for x in current}
        for item in file_list:
            if item.get("filename", "").lower() not in existing_names:
                current.append(item)
                existing_names.add(item.get("filename", "").lower())

        with open(phone_index_file, 'w', encoding='utf-8') as f:
            json.dump(current, f, indent=4, ensure_ascii=False)
        return len(current)
    except Exception as e:
        print(f"Erreur enregistrement musique téléphone: {e}")
        return 0

def verify_track_artist(track_title: str, track_artist: str, target_singer: str) -> dict:
    """
    Scanner vérificateur de chanteur :
    Vérifie qu'un morceau appartient BIEN et LÉGITIMEMENT au chanteur sélectionné.
    Élimine les reprises amateurs, parodies, hommages, ou titres mal attribués.
    """
    norm_target = normalize_string(target_singer)
    norm_artist = normalize_string(track_artist)
    norm_title = normalize_string(track_title)

    # 1. Détection de reprises / parodies / hommages dans le titre ou l'artiste
    cover_keywords = [
        'tribute', 'hommage', 'cover', 'reprise', 'karaoke', 'instrumental',
        'inthestyleof', 'styleof', 'originallyperformed', 'acappella', 'parodie'
    ]
    raw_lower = f"{track_title} {track_artist}".lower()
    for kw in cover_keywords:
        if kw in norm_title or kw in norm_artist or kw in raw_lower:
            return {
                "is_verified": False,
                "status": "COVER_OR_TRIBUTE",
                "target_singer": target_singer,
                "official_artist": track_artist,
                "confidence": 10,
                "badge": "⚠️ Reprise / Hommage non officiel",
                "message": f"Ce titre semble être une reprise ou un hommage et n'est pas la version officielle de {target_singer}."
            }

    # 2. Vérification directe du nom d'artiste si fourni
    if norm_artist and norm_target:
        # Correspondance exacte ou inclusion mutuelle forte
        if norm_artist == norm_target or (len(norm_target) >= 4 and norm_target in norm_artist):
            is_main = True
        elif len(norm_artist) >= 4 and norm_artist in norm_target:
            is_main = True
        else:
            is_main = False
    else:
        is_main = False

    # 3. Interrogation du catalogue officiel (iTunes API) pour vérifier l'authenticité de l'interprète
    try:
        url = "https://itunes.apple.com/search"
        params = {
            "term": f"{target_singer} {track_title}",
            "entity": "song",
            "limit": 5
        }
        resp = requests.get(url, params=params, timeout=4)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            for item in results:
                itunes_artist = item.get("artistName", "")
                itunes_title = item.get("trackName", "")
                norm_itunes_a = normalize_string(itunes_artist)

                # Si le titre concorde et que l'artiste officiel iTunes correspond à notre chanteur cible
                if is_duplicate_title(track_title, itunes_title):
                    if norm_target in norm_itunes_a or norm_itunes_a in norm_target:
                        return {
                            "is_verified": True,
                            "status": "VERIFIED_OFFICIAL",
                            "target_singer": target_singer,
                            "official_artist": itunes_artist,
                            "official_title": itunes_title,
                            "album": item.get("collectionName", ""),
                            "confidence": 100,
                            "badge": f"✅ Morceau officiel vérifié ({itunes_artist})",
                            "message": f"Authentifié : ce titre appartient bien au catalogue officiel de {target_singer}."
                        }
                    else:
                        # Le titre existe mais appartient officiellement à un autre artiste !
                        return {
                            "is_verified": False,
                            "status": "DIFFERENT_ARTIST",
                            "target_singer": target_singer,
                            "official_artist": itunes_artist,
                            "official_title": itunes_title,
                            "confidence": 20,
                            "badge": f"❌ Chanteur différent : {itunes_artist}",
                            "message": f"Attention : ce titre appartient officiellement à '{itunes_artist}' et non à '{target_singer}'."
                        }
    except Exception as e:
        pass

    # Si l'API n'a pas répondu mais que les noms concordent
    if is_main:
        return {
            "is_verified": True,
            "status": "NAME_MATCH",
            "target_singer": target_singer,
            "official_artist": track_artist or target_singer,
            "confidence": 85,
            "badge": f"✅ Appartient à {target_singer}",
            "message": f"Le nom de l'artiste correspond à {target_singer}."
        }

    return {
        "is_verified": False,
        "status": "UNCERTAIN",
        "target_singer": target_singer,
        "official_artist": track_artist or "Inconnu",
        "confidence": 40,
        "badge": "⚠️ Chanteur non garanti",
        "message": f"Impossible de certifier que ce morceau appartient à {target_singer} (Artiste détecté : {track_artist})."
    }

def scan_and_verify_singer_folder(target_singer: str) -> dict:
    """
    Scanne tous les fichiers MP3 dans le dossier du chanteur et vérifie
    si chacun appartient RÉELLEMENT au chanteur choisi.
    Détecte les intrus et propose les corrections.
    """
    cfg = load_config()
    music_base = cfg.get("music_folder", "Musique")
    clean_artist = sanitize_filename(target_singer)
    artist_dir = os.path.join(music_base, clean_artist)

    verified_tracks = []
    intruder_tracks = []
    total_scanned = 0

    if os.path.exists(artist_dir):
        for f in os.listdir(artist_dir):
            if f.lower().endswith(('.mp3', '.m4a', '.flac', '.ogg', '.wav')):
                total_scanned += 1
                full_path = os.path.join(artist_dir, f)
                meta = read_mp3_tags(full_path)
                title = meta.get("title") or os.path.splitext(f)[0]
                artist = meta.get("artist") or target_singer

                verification = verify_track_artist(title, artist, target_singer)
                track_info = {
                    "filename": f,
                    "rel_path": f"{clean_artist}/{f}",
                    "title": title,
                    "artist": artist,
                    "verification": verification
                }

                if verification.get("is_verified"):
                    verified_tracks.append(track_info)
                else:
                    intruder_tracks.append(track_info)

    return {
        "target_singer": target_singer,
        "folder": artist_dir,
        "total_scanned": total_scanned,
        "verified_count": len(verified_tracks),
        "intruder_count": len(intruder_tracks),
        "verified_tracks": verified_tracks,
        "intruder_tracks": intruder_tracks
    }

