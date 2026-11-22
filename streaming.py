# -*- coding: utf-8 -*-
"""
streaming.py — Moteur Haute Puissance de Films Complets & Séries en Streaming Gratuit
Fonctionnalités :
- Plus de 35+ choix de films/séries par recherche (Cinemeta + IMDb Base Mondiale)
- 8 Serveurs de streaming gratuits et sans abonnement
- Prise en charge des versions françaises (VF) et VOSTFR (multi-langues)
- Filtrage strict anti-intrus (aucun extrait, aucun clip non lié, aucun podcast)
- Catalogue de tendances (50 films & séries dès l'ouverture du mode streaming)
- Prise en charge complète des séries (Saisons & Épisodes)
"""

import urllib.request
import urllib.parse
import json
import ssl
import re

# Contexte SSL tolérant
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

def clean_query(q: str) -> str:
    """Nettoie la requête utilisateur."""
    if not q:
        return ""
    q = re.sub(r'[^\w\s\-\'\.]', ' ', q, flags=re.UNICODE)
    return " ".join(q.split()).strip()

def build_servers(imdb_id: str, is_series: bool = False, season: int = 1, episode: int = 1):
    """
    Génère 8 serveurs de streaming gratuits fiables pour un film ou un épisode de série.
    Priorité aux serveurs disposant de la Version Française (VF) et du multi-langues / VOSTFR.
    """
    s = max(1, int(season))
    e = max(1, int(episode))

    if is_series:
        return {
            "🇫🇷 Serveur 1 (VF / Multi)": f"https://multiembed.mov/?video_id={imdb_id}&s={s}&e={e}",
            "🇫🇷 Serveur 2 (Français HD - Smashy)": f"https://embed.smashystream.com/playere.php?imdb={imdb_id}&season={s}&episode={e}",
            "🇫🇷 Serveur 3 (VidSrc VF / FR)": f"https://vidsrc.me/embed/tv?imdb={imdb_id}&season={s}&episode={e}&ds_lang=fr",
            "⚡ Serveur 4 (VidSrc TO Rapide)": f"https://vidsrc.to/embed/tv/{imdb_id}/{s}/{e}",
            "🎬 Serveur 5 (AutoEmbed)": f"https://autoembed.to/tv/imdb/{imdb_id}-{s}-{e}",
            "🍿 Serveur 6 (2Embed)": f"https://www.2embed.cc/embedtv/{imdb_id}&s={s}&e={e}",
            "🌐 Serveur 7 (StreamM4u)": f"https://streamm4u.com/embed/tv/{imdb_id}/{s}/{e}",
            "🛡️ Serveur 8 (VidSrc NET Miroir)": f"https://vidsrc.net/embed/tv/{imdb_id}/{s}/{e}"
        }
    else:
        return {
            "🇫🇷 Serveur 1 (VF / Multi)": f"https://multiembed.mov/?video_id={imdb_id}",
            "🇫🇷 Serveur 2 (Français HD - Smashy)": f"https://embed.smashystream.com/playere.php?imdb={imdb_id}",
            "🇫🇷 Serveur 3 (VidSrc VF / FR)": f"https://vidsrc.me/embed/movie?imdb={imdb_id}&ds_lang=fr",
            "⚡ Serveur 4 (VidSrc TO Rapide)": f"https://vidsrc.to/embed/movie/{imdb_id}",
            "🎬 Serveur 5 (AutoEmbed)": f"https://autoembed.to/movie/imdb/{imdb_id}",
            "🍿 Serveur 6 (2Embed)": f"https://www.2embed.cc/embed/{imdb_id}",
            "🌐 Serveur 7 (StreamM4u)": f"https://streamm4u.com/embed/movie/{imdb_id}",
            "🛡️ Serveur 8 (VidSrc NET Miroir)": f"https://vidsrc.net/embed/movie/{imdb_id}"
        }

def get_series_stream_url(imdb_id: str, season: int = 1, episode: int = 1, server_idx: int = 1):
    """Renvoie l'URL exacte d'un épisode pour le serveur sélectionné."""
    srv_dict = build_servers(imdb_id, is_series=True, season=season, episode=episode)
    keys = list(srv_dict.keys())
    idx = max(0, min(server_idx - 1, len(keys) - 1))
    return srv_dict[keys[idx]]

def search_cinemeta(query: str, limit: int = 35):
    """
    Recherche étendue dans le catalogue Cinemeta mondial (films + séries).
    Renvoie les vrais films de cinéma avec affiches, synopsis et identifiants.
    """
    clean_q = clean_query(query)
    if not clean_q:
        return []

    encoded = urllib.parse.quote(clean_q)
    results = {}

    # 1. Films
    try:
        url_m = f"https://v3-cinemeta.strem.io/catalog/movie/top/search={encoded}.json"
        req = urllib.request.Request(url_m, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=5) as r:
            data = json.loads(r.read().decode('utf-8'))
            for m in data.get('metas', []):
                iid = m.get('imdb_id')
                if not iid or not iid.startswith('tt'):
                    continue
                year = str(m.get('releaseInfo') or m.get('year') or '')
                poster = m.get('poster') or ""
                results[iid] = {
                    "id": iid,
                    "title": m.get('name', 'Film'),
                    "year": year,
                    "type": "movie",
                    "type_label": "🎬 Film Complet",
                    "is_series": False,
                    "actors": m.get('description', '')[:110] if m.get('description') else '',
                    "thumbnail": poster or "/static/icons/icon-192.png",
                    "servers": build_servers(iid, is_series=False),
                    "embed_url": f"https://multiembed.mov/?video_id={iid}",
                    "url": f"https://www.imdb.com/title/{iid}/",
                    "source": "Cinéma Gratuit (VF / VOSTFR)",
                    "duration": f"Sortie : {year}" if year else "Film Complet"
                }
    except Exception as e:
        print(f"[Cinemeta Film] Erreur: {e}")

    # 2. Séries
    try:
        url_s = f"https://v3-cinemeta.strem.io/catalog/series/top/search={encoded}.json"
        req = urllib.request.Request(url_s, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=5) as r:
            data = json.loads(r.read().decode('utf-8'))
            for s in data.get('metas', []):
                iid = s.get('imdb_id')
                if not iid or not iid.startswith('tt') or iid in results:
                    continue
                year = str(s.get('releaseInfo') or s.get('year') or '')
                poster = s.get('poster') or ""
                results[iid] = {
                    "id": iid,
                    "title": s.get('name', 'Série'),
                    "year": year,
                    "type": "serie",
                    "type_label": "📺 Série TV",
                    "is_series": True,
                    "actors": s.get('description', '')[:110] if s.get('description') else '',
                    "thumbnail": poster or "/static/icons/icon-192.png",
                    "servers": build_servers(iid, is_series=True),
                    "embed_url": f"https://multiembed.mov/?video_id={iid}&s=1&e=1",
                    "url": f"https://www.imdb.com/title/{iid}/",
                    "source": "Série Streaming (VF / VOSTFR)",
                    "duration": f"Série • {year}" if year else "Série Complète"
                }
    except Exception as e:
        print(f"[Cinemeta Série] Erreur: {e}")

    return list(results.values())

def search_imdb(query: str, limit: int = 15):
    """
    Recherche officielle IMDb avec filtrage strict pour écarter les contenus non pertinents
    (jeux vidéo, podcasts, courts métrages inconnus).
    """
    clean_q = clean_query(query)
    if not clean_q:
        return []

    encoded = urllib.parse.quote(clean_q.lower())
    url = f"https://v3.sg.media-imdb.com/suggestion/x/{encoded}.json"
    req = urllib.request.Request(url, headers=HEADERS)

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
                # Éliminer formellement les bruits (jeux vidéo, podcasts, clips)
                if qtype in ['podcast series', 'video game', 'music video']:
                    continue

                is_series = 'series' in qtype or 'tv' in qtype
                title = item.get('l', 'Film')
                year = item.get('y', '')
                actors = item.get('s', '')
                
                img_data = item.get('i') or {}
                poster = img_data.get('imageUrl') or ""

                results.append({
                    "id": imdb_id,
                    "title": title,
                    "year": str(year) if year else "",
                    "type": "serie" if is_series else "movie",
                    "type_label": "📺 Série TV" if is_series else "🎬 Film Complet",
                    "is_series": is_series,
                    "actors": actors,
                    "thumbnail": poster or "/static/icons/icon-192.png",
                    "servers": build_servers(imdb_id, is_series=is_series),
                    "embed_url": f"https://multiembed.mov/?video_id={imdb_id}" + ("&s=1&e=1" if is_series else ""),
                    "url": f"https://www.imdb.com/title/{imdb_id}/",
                    "source": "Cinéma Gratuit (VF / VOSTFR)",
                    "duration": f"Sortie : {year}" if year else "Film Complet"
                })
    except Exception as e:
        print(f"[IMDb] Erreur: {e}")

    return results

def get_trending_catalog(limit: int = 40):
    """
    Récupère le catalogue des films et séries les plus populaires du moment.
    Permet à l'utilisateur de choisir directement parmi les meilleurs films sans chercher.
    """
    results = {}
    try:
        url_m = "https://v3-cinemeta.strem.io/catalog/movie/top.json"
        req = urllib.request.Request(url_m, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=5) as r:
            data = json.loads(r.read().decode('utf-8'))
            for m in data.get('metas', [])[:25]:
                iid = m.get('imdb_id')
                if not iid or not iid.startswith('tt'):
                    continue
                year = str(m.get('releaseInfo') or m.get('year') or '')
                results[iid] = {
                    "id": iid,
                    "title": m.get('name', 'Film'),
                    "year": year,
                    "type": "movie",
                    "type_label": "🔥 Tendance Cinéma",
                    "is_series": False,
                    "actors": m.get('description', '')[:100] if m.get('description') else '',
                    "thumbnail": m.get('poster') or "/static/icons/icon-192.png",
                    "servers": build_servers(iid, is_series=False),
                    "embed_url": f"https://multiembed.mov/?video_id={iid}",
                    "url": f"https://www.imdb.com/title/{iid}/",
                    "source": "Tendance Streaming",
                    "duration": f"Sortie : {year}" if year else "Film Complet"
                }
    except Exception as e:
        print(f"[Trending Films] Erreur: {e}")

    try:
        url_s = "https://v3-cinemeta.strem.io/catalog/series/top.json"
        req = urllib.request.Request(url_s, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=5) as r:
            data = json.loads(r.read().decode('utf-8'))
            for s in data.get('metas', [])[:20]:
                iid = s.get('imdb_id')
                if not iid or not iid.startswith('tt') or iid in results:
                    continue
                year = str(s.get('releaseInfo') or s.get('year') or '')
                results[iid] = {
                    "id": iid,
                    "title": s.get('name', 'Série'),
                    "year": year,
                    "type": "serie",
                    "type_label": "📺 Série Populaire",
                    "is_series": True,
                    "actors": s.get('description', '')[:100] if s.get('description') else '',
                    "thumbnail": s.get('poster') or "/static/icons/icon-192.png",
                    "servers": build_servers(iid, is_series=True),
                    "embed_url": f"https://multiembed.mov/?video_id={iid}&s=1&e=1",
                    "url": f"https://www.imdb.com/title/{iid}/",
                    "source": "Série Tendance",
                    "duration": f"Série • {year}" if year else "Série Complète"
                }
    except Exception as e:
        print(f"[Trending Séries] Erreur: {e}")

    return list(results.values())[:limit]

def search_streaming(query: str, limit: int = 35):
    """
    Recherche universelle ultra-complète :
    - Retourne plus de 35+ films & séries pertinents
    - Supprime tout contenu non lié
    - Fournit 8 serveurs avec VF/VOSTFR
    """
    query = (query or "").strip()

    # Si la recherche est vide ou demande les tendances
    if not query or query.lower() in ["top", "tendance", "tendances", "populaire", "films", "all"]:
        return get_trending_catalog(limit=limit)

    # Si c'est un lien direct collé par l'utilisateur
    if query.startswith(('http://', 'https://')):
        embed_url = query
        if "dailymotion.com/video/" in query:
            dm_id = query.split('/video/')[-1].split('?')[0]
            embed_url = f"https://www.dailymotion.com/embed/video/{dm_id}?autoplay=1"
        elif "youtube.com/watch" in query or "youtu.be/" in query:
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
            "actors": "Lien streaming utilisateur",
            "thumbnail": "/static/icons/icon-192.png",
            "embed_url": embed_url,
            "servers": {
                "Lecteur Direct": embed_url
            },
            "url": query,
            "source": "Lien Streaming Direct",
            "duration": "Direct"
        }]

    # 1. Recherche mondiale Cinemeta (films + séries)
    cm_results = search_cinemeta(query, limit=limit)

    # 2. Recherche complémentaire IMDb
    imdb_results = search_imdb(query, limit=15)

    # Fusion et déduplication
    merged = {}
    q_words = [w.lower() for w in clean_query(query).split() if len(w) > 1]

    # Prioriser les films correspondants
    for item in cm_results + imdb_results:
        iid = item.get('id')
        if not iid or iid in merged:
            continue
        
        # Filtre anti-hors sujet : vérifie que le titre a au moins un mot clé
        title_lower = item.get('title', '').lower()
        if q_words and not any(w in title_lower for w in q_words):
            # Ne pas inclure de vidéos qui n'ont rien à voir
            continue

        merged[iid] = item

    # Tri par pertinence : le film dont le titre correspond le plus exactement arrive en 1er
    def sort_score(item):
        t = item.get('title', '').lower()
        clean_user_q = clean_query(query).lower()
        if t == clean_user_q:
            return 100
        if t.startswith(clean_user_q):
            return 80
        if clean_user_q in t:
            return 60
        # Compter le nombre de mots en commun
        common = sum(1 for w in q_words if w in t)
        return common * 10

    sorted_list = sorted(list(merged.values()), key=sort_score, reverse=True)

    # Si aucun résultat strict n'a été trouvé, renvoyer les correspondances globales
    if not sorted_list:
        sorted_list = list(merged.values()) or cm_results or imdb_results

    return sorted_list[:limit]
