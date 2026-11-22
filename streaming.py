# -*- coding: utf-8 -*-
"""
streaming.py — Moteur de recherche et lecteur de VRAIS FILMS & SÉRIES en streaming gratuit
Prend en charge :
- Recherche dans la base mondiale de films et séries (IMDb / Cinéma)
- Fournisseurs de streaming complets sans publicité intrusive (MultiEmbed, VidSrc, 2Embed, AutoEmbed)
- Prise en charge des versions françaises (VF) et VOSTFR (multi-langues)
- Prise en charge des séries avec sélecteur de saisons & épisodes
- Recherche de films complets en français sur Dailymotion
- Extraction et lecture de liens de streaming directs (Uqload, Doodstream, Dailymotion, Archive.org, etc.)
"""

import urllib.request
import urllib.parse
import json
import ssl
import re

# Contexte SSL tolérant pour les serveurs multimédias
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

def clean_query(q: str) -> str:
    """Nettoie la requête de recherche."""
    if not q:
        return ""
    q = re.sub(r'[^\w\s\-\'\.]', ' ', q, flags=re.UNICODE)
    return " ".join(q.split()).strip()

def search_imdb_movies(query: str, limit: int = 10):
    """
    Recherche des films et séries officiels dans la base mondiale IMDb.
    Renvoie les films avec affiche, année, acteurs et identifiant IMDb (tt...).
    """
    clean_q = clean_query(query)
    if not clean_q:
        return []

    # API suggestion IMDb officielle (gratuite, sans clé, ultra rapide)
    encoded = urllib.parse.quote(clean_q.lower())
    url = f"https://v3.sg.media-imdb.com/suggestion/x/{encoded}.json"
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        }
    )

    results = []
    try:
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            items = data.get('d', [])
            for item in items:
                imdb_id = item.get('id', '')
                if not imdb_id.startswith('tt'):
                    continue

                qtype = (item.get('q') or '').lower()
                # Filtrer les types pertinents (films, séries, documentaires)
                is_series = 'series' in qtype or 'tv' in qtype
                if qtype and qtype not in ['feature', 'tv series', 'tv mini-series', 'tv movie', 'video', 'movie']:
                    continue

                title = item.get('l', 'Film')
                year = item.get('y', '')
                actors = item.get('s', '')
                
                # Image d'affiche haute définition
                img_data = item.get('i') or {}
                poster = img_data.get('imageUrl') or ""

                type_label = "📺 Série TV" if is_series else "🎬 Film Complet"

                # Génération des différents serveurs de streaming gratuits
                if is_series:
                    servers = {
                        "Serveur 1 (VF / Multi)": f"https://multiembed.mov/?video_id={imdb_id}&s=1&e=1",
                        "Serveur 2 (VidSrc)": f"https://vidsrc.me/embed/tv?imdb={imdb_id}&season=1&episode=1",
                        "Serveur 3 (VidSrc TO)": f"https://vidsrc.to/embed/tv/{imdb_id}/1/1",
                        "Serveur 4 (AutoEmbed)": f"https://autoembed.to/tv/imdb/{imdb_id}-1-1"
                    }
                    default_embed = servers["Serveur 1 (VF / Multi)"]
                else:
                    servers = {
                        "Serveur 1 (VF / Multi)": f"https://multiembed.mov/?video_id={imdb_id}",
                        "Serveur 2 (VidSrc)": f"https://vidsrc.me/embed/movie?imdb={imdb_id}",
                        "Serveur 3 (VidSrc TO)": f"https://vidsrc.to/embed/movie/{imdb_id}",
                        "Serveur 4 (2Embed)": f"https://www.2embed.cc/embed/{imdb_id}",
                        "Serveur 5 (AutoEmbed)": f"https://autoembed.to/movie/imdb/{imdb_id}"
                    }
                    default_embed = servers["Serveur 1 (VF / Multi)"]

                results.append({
                    "id": imdb_id,
                    "title": title,
                    "year": str(year) if year else "",
                    "type": "serie" if is_series else "movie",
                    "type_label": type_label,
                    "is_series": is_series,
                    "actors": actors,
                    "thumbnail": poster or "/static/icons/icon-192.png",
                    "embed_url": default_embed,
                    "servers": servers,
                    "url": f"https://www.imdb.com/title/{imdb_id}/",
                    "source": "Streaming Cinéma (VF / VOSTFR)",
                    "duration": f"Sortie : {year}" if year else "Film Complet"
                })

                if len(results) >= limit:
                    break
    except Exception as e:
        print(f"[Streaming] Erreur recherche IMDb: {e}")

    return results

def search_dailymotion_movies(query: str, limit: int = 5):
    """
    Recherche des films complets hébergés sur Dailymotion en français.
    """
    clean_q = clean_query(query)
    if not clean_q:
        return []

    search_phrase = f"{clean_q} film complet francais"
    encoded = urllib.parse.quote(search_phrase)
    url = f"https://api.dailymotion.com/videos?search={encoded}&fields=id,title,thumbnail_720_url,thumbnail_480_url,duration,owner.screenname&limit={limit}"
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    )

    results = []
    try:
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            items = data.get('list', [])
            for item in items:
                vid_id = item.get('id')
                if not vid_id:
                    continue
                title = item.get('title', 'Film Dailymotion')
                duration_sec = item.get('duration', 0)
                
                # Format durée
                mins = duration_sec // 60
                secs = duration_sec % 60
                dur_str = f"{mins:02d}:{secs:02d}"

                thumb = item.get('thumbnail_720_url') or item.get('thumbnail_480_url') or "/static/icons/icon-192.png"
                uploader = item.get('owner.screenname', 'Dailymotion')
                embed_url = f"https://www.dailymotion.com/embed/video/{vid_id}?autoplay=1"
                web_url = f"https://www.dailymotion.com/video/{vid_id}"

                results.append({
                    "id": f"dm_{vid_id}",
                    "title": title,
                    "year": "",
                    "type": "movie",
                    "type_label": "🎬 Film VF (Dailymotion)",
                    "is_series": False,
                    "actors": uploader,
                    "thumbnail": thumb,
                    "embed_url": embed_url,
                    "servers": {
                        "Lecteur Dailymotion": embed_url
                    },
                    "url": web_url,
                    "source": "Dailymotion Film",
                    "duration": dur_str
                })
    except Exception as e:
        print(f"[Streaming] Erreur Dailymotion: {e}")

    return results

def search_streaming(query: str, limit: int = 15):
    """
    Recherche universelle de streaming :
    1. Si URL directe collée par l'utilisateur -> détection et streaming direct.
    2. Recherche des vrais films et séries du cinéma avec lecteurs streaming gratuits multi-serveurs (VF/VOSTFR).
    3. Recherche complémentaire Dailymotion films complets.
    """
    query = (query or "").strip()
    if not query:
        return []

    # 1. Cas d'une URL collée par l'utilisateur
    if query.startswith(('http://', 'https://')):
        # Lien direct
        embed_url = query
        # Support Dailymotion embed
        if "dailymotion.com/video/" in query:
            dm_id = query.split('/video/')[-1].split('?')[0]
            embed_url = f"https://www.dailymotion.com/embed/video/{dm_id}?autoplay=1"
        elif "youtube.com/watch" in query or "youtu.be/" in query:
            # Si lien youtube direct
            m = re.search(r'(?:v=|youtu\.be/)([\w\-]+)', query)
            if m:
                embed_url = f"https://www.youtube-nocookie.com/embed/{m.group(1)}?autoplay=1&playsinline=1"

        return [{
            "id": "direct_link",
            "title": "Flux Streaming Direct",
            "year": "",
            "type": "video",
            "type_label": "📺 Flux Direct",
            "is_series": False,
            "actors": "Lien utilisateur",
            "thumbnail": "/static/icons/icon-192.png",
            "embed_url": embed_url,
            "servers": {
                "Lecteur Direct": embed_url
            },
            "url": query,
            "source": "Lien Streaming Direct",
            "duration": "Direct"
        }]

    # 2. Recherche films et séries cinéma dans la base mondiale avec lecteurs multi-serveurs
    movies = search_imdb_movies(query, limit=limit)

    # 3. Recherche complémentaire sur Dailymotion pour trouver des versions françaises intégrales
    dm_movies = search_dailymotion_movies(query, limit=4)

    # Fusionner en priorisant les vrais films de cinéma
    combined = list(movies) + list(dm_movies)
    return combined[:limit]

def get_series_stream_url(imdb_id: str, season: int = 1, episode: int = 1, server_idx: int = 1):
    """
    Génère l'URL d'un épisode spécifique d'une série pour le serveur choisi.
    """
    s = max(1, int(season))
    e = max(1, int(episode))

    if server_idx == 1:
        return f"https://multiembed.mov/?video_id={imdb_id}&s={s}&e={e}"
    elif server_idx == 2:
        return f"https://vidsrc.me/embed/tv?imdb={imdb_id}&season={s}&episode={e}"
    elif server_idx == 3:
        return f"https://vidsrc.to/embed/tv/{imdb_id}/{s}/{e}"
    elif server_idx == 4:
        return f"https://autoembed.to/tv/imdb/{imdb_id}-{s}-{e}"
    return f"https://multiembed.mov/?video_id={imdb_id}&s={s}&e={e}"
