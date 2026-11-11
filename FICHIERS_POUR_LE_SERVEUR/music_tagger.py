import os
import re
import requests
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TPE2, TALB, APIC, ID3NoHeaderError

def sanitize_filename(name: str) -> str:
    """Nettoie les caractères interdits pour les fichiers et dossiers Windows."""
    if not name:
        return "Inconnu"
    # Supprime les caractères interdits sous Windows: < > : " / \ | ? *
    cleaned = re.sub(r'[<>:"/\\|?*]', '', name)
    # Supprime les espaces multiples et les points finaux
    cleaned = re.sub(r'\s+', ' ', cleaned).strip('. ')
    return cleaned if cleaned else "Inconnu"

def clean_noise_from_title(title: str) -> str:
    """Supprime les mentions parasites fréquentes dans les titres YouTube/vidéos."""
    noise_patterns = [
        # Formats complexes (Vidéo officielle remasterisée en HD, Clip Officiel 4K, etc.)
        r'[\(\[\{]\s*(?:vid[eé]o\s*officielle|clip\s*officiel|official\s*(?:music\s*)?video|official\s*audio|audio\s*officiel|lyric\s*video|clip|lyrics|paroles|visualizer)[^\)\]\}]*[\)\]\}]',
        r'[\(\[\{]\s*(?:remaster[^\)\]\}]*|version\s*originale|live[^\)\]\}]*|hd|4k|hq)\s*[\)\]\}]',
        r'(?:official\s*(?:music\s*)?video|clip\s*officiel|official\s*audio|audio\s*officiel|lyric\s*video)',
        r'[\(\[\{]\s*(?:paroles\s*et\s*musique|sub\s*ita|sub\s*esp|sub\s*fr)\s*[\)\]\}]',
    ]
    cleaned = title
    for pat in noise_patterns:
        cleaned = re.sub(pat, '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip(' -–—:_')
    return cleaned

def clean_artist_name(artist: str) -> str:
    """Nettoie le nom du chanteur (retire VEVO, Topic, etc.)."""
    if not artist:
        return "Artiste Inconnu"
    cleaned = re.sub(r'VEVO$', '', artist, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*-\s*Topic$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*Official$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip(' -–—:_')
    return cleaned if cleaned else "Artiste Inconnu"

def parse_artist_and_title(raw_title: str, uploader: str = None, metadata_artist: str = None, metadata_track: str = None):
    """
    Détecte intelligemment le chanteur et le titre du morceau.
    Priorités :
    1. Métadonnées officielles (si disponibles)
    2. Détection du format 'Chanteur - Titre' dans le titre brut
    3. Si pas de tiret, le chanteur est l'uploader (chaîne) et le titre est le titre nettoyé
    """
    # 1. Si métadonnées directes fiables
    if metadata_artist and metadata_track:
        return clean_artist_name(metadata_artist), clean_noise_from_title(metadata_track)

    clean_raw = clean_noise_from_title(raw_title)

    # 2. Séparateurs fréquents : "Artiste - Titre", "Artiste – Titre", "Artiste : Titre"
    separators = [r'\s+-\s+', r'\s+–\s+', r'\s+—\s+', r'\s+:\s+']
    for sep in separators:
        parts = re.split(sep, clean_raw, maxsplit=1)
        if len(parts) == 2:
            artist_part = clean_artist_name(parts[0].strip())
            title_part = clean_noise_from_title(parts[1].strip())
            if artist_part and title_part:
                return artist_part, title_part

    # 3. Fallback : uploader comme chanteur
    if uploader:
        cleaned_uploader = clean_artist_name(uploader)
        return cleaned_uploader, clean_raw

    return "Artiste Inconnu", clean_raw

def tag_mp3(file_path: str, artist: str, title: str, album: str = None, cover_data: bytes = None, cover_url: str = None):
    """
    Écrit les métadonnées ID3 dans le fichier MP3 pour que le lecteur de musique
    ('app music' sur téléphone ou ordinateur) affiche immédiatement le chanteur,
    le titre et la pochette.
    """
    try:
        audio = MP3(file_path, ID3=ID3)
        try:
            audio.add_tags()
        except Exception:
            pass

        # Nom du chanteur (Artiste principal)
        if artist:
            audio.tags.setall('TPE1', [TPE1(encoding=3, text=artist)])
            audio.tags.setall('TPE2', [TPE2(encoding=3, text=artist)]) # Album artist

        # Titre du morceau
        if title:
            audio.tags.setall('TIT2', [TIT2(encoding=3, text=title)])

        # Album
        album_name = album if album else f"{artist} Singles"
        audio.tags.setall('TALB', [TALB(encoding=3, text=album_name)])

        # Téléchargement de la pochette si nécessaire
        img_bytes = cover_data
        if not img_bytes and cover_url:
            try:
                resp = requests.get(cover_url, timeout=10)
                if resp.status_code == 200:
                    img_bytes = resp.content
            except Exception as e:
                print(f"Impossible de télécharger la pochette : {e}")

        # Intégration de la pochette ID3 APIC
        if img_bytes:
            mime = 'image/jpeg'
            if img_bytes.startswith(b'\x89PNG'):
                mime = 'image/png'
            audio.tags.setall('APIC', [
                APIC(
                    encoding=3,
                    mime=mime,
                    type=3, # Cover (front)
                    desc='Front Cover',
                    data=img_bytes
                )
            ])

        audio.save()
        return True
    except Exception as e:
        print(f"Erreur lors de l'application des tags ID3 sur {file_path}: {e}")
        return False

def read_mp3_tags(file_path: str):
    """Lit les tags ID3 d'un fichier MP3."""
    try:
        audio = MP3(file_path)
        artist = "Artiste Inconnu"
        title = os.path.splitext(os.path.basename(file_path))[0]
        album = ""
        has_cover = False

        if audio.tags:
            if 'TPE1' in audio.tags:
                artist = str(audio.tags['TPE1'])
            if 'TIT2' in audio.tags:
                title = str(audio.tags['TIT2'])
            if 'TALB' in audio.tags:
                album = str(audio.tags['TALB'])
            for key in audio.tags.keys():
                if key.startswith('APIC'):
                    has_cover = True
                    break

        duration = int(audio.info.length) if audio.info else 0
        bitrate = int(audio.info.bitrate / 1000) if audio.info else 0

        return {
            "artist": artist,
            "title": title,
            "album": album,
            "duration": duration,
            "bitrate": bitrate,
            "has_cover": has_cover
        }
    except Exception:
        # Fallback silencieux sur le nom du fichier si le tag ID3 est corrompu ou absent
        return {
            "artist": "Artiste Inconnu",
            "title": os.path.splitext(os.path.basename(file_path))[0],
            "album": "",
            "duration": 0,
            "bitrate": 0,
            "has_cover": False
        }
