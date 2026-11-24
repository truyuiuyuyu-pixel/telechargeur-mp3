# -*- coding: utf-8 -*-
"""
streaming.py — Moteur Haute Puissance de Films Complets, Séries & Bandes-Annonces
Style Disney+ & Box-Office Mondial
Intègre de VRAIS serveurs français (VF / VOSTFR) et exclusion stricte des musiques.
"""

import urllib.request
import urllib.parse
import json
import ssl
import re

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

# Filtre strict anti-musique : aucune chanson, bande son, album ou clip en mode streaming
MUSIC_FILTER_RE = re.compile(
    r'\b(music video|soundtrack|clip officiel|song|chanson|ost|audio track|album|single|concert|clip|paroles|karaoke|bande originale)\b',
    re.IGNORECASE
)

# Cache mémoire rapide pour convertir instantanément IMDb ID en TMDB ID
TMDB_CACHE = {}

def get_tmdb_id(imdb_id: str, is_series: bool = False) -> str:
    """Récupère l'identifiant TMDB correspondant à un IMDb ID."""
    if not imdb_id or not imdb_id.startswith('tt'):
        return ""
    if imdb_id in TMDB_CACHE:
        return TMDB_CACHE[imdb_id]

    try:
        mtype = "series" if is_series else "movie"
        url = f"https://v3-cinemeta.strem.io/meta/{mtype}/{imdb_id}.json"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=2.5) as r:
            data = json.loads(r.read().decode('utf-8'))
            mid = data.get('meta', {}).get('moviedb_id')
            if mid:
                TMDB_CACHE[imdb_id] = str(mid)
                return str(mid)
    except Exception:
        pass
    return ""

def clean_query(q: str) -> str:
    """Nettoie la requête utilisateur."""
    if not q:
        return ""
    q = re.sub(r'[^\w\s\-\'\.]', ' ', q, flags=re.UNICODE)
    return " ".join(q.split()).strip()

def build_servers(imdb_id: str, tmdb_id: str = "", title: str = "", is_series: bool = False, season: int = 1, episode: int = 1):
    """
    Génère les serveurs de streaming fiables en français (VF & VOSTFR).
    Intègre les endpoints Frembed actifs, les serveurs multi-pistes et les recherches VF directes débloquées.
    """
    s = max(1, int(season))
    e = max(1, int(episode))

    if not tmdb_id:
        if imdb_id in TMDB_CACHE:
            tmdb_id = TMDB_CACHE[imdb_id]
        elif imdb_id and imdb_id.startswith('tt'):
            tmdb_id = get_tmdb_id(imdb_id, is_series=is_series)

    servers = {}
    clean_title = (title or "").strip()

    if is_series:
        if tmdb_id:
            servers["1. 🇫🇷 Serveur 1 (Frembed VF)"] = f"https://frembed.pics/embed/serie/{tmdb_id}?sa={s}&epi={e}"
            servers["2. 🇫🇷 Serveur 2 (Frembed Miroir)"] = f"https://frembed.shop/api/serie.php?id={tmdb_id}&sa={s}&epi={e}"

        servers["3. 🇫🇷 Serveur 3 (Smashy Audio FR)"] = f"https://embed.smashystream.com/playere.php?imdb={imdb_id}&season={s}&episode={e}"
        servers["4. 🇫🇷 Serveur 4 (VidSrc Audio/ST FR)"] = f"https://vidsrc.me/embed/tv?imdb={imdb_id}&season={s}&episode={e}&ds_lang=fr"

        if clean_title:
            q_enc = urllib.parse.quote(clean_title)
            servers["5. 🍿 Serveur 5 (Wiflix VF Direct)"] = f"/api/streaming/proxy?url={urllib.parse.quote('https://wiflix.voto/?s=' + q_enc)}"
            servers["6. 🎬 Serveur 6 (French-Stream VF)"] = f"/api/streaming/proxy?url={urllib.parse.quote('https://french-stream.bio/?s=' + q_enc)}"

        servers["7. 🌐 Serveur 7 (MultiEmbed Multi)"] = f"https://multiembed.mov/?video_id={imdb_id}&s={s}&e={e}"
        servers["8. 🍿 Serveur 8 (2Embed Cinéma)"] = f"https://www.2embed.cc/embedtv/{imdb_id}&s={s}&e={e}"
        servers["9. ⚡ Serveur 9 (AutoEmbed Rapide)"] = f"https://autoembed.to/tv/imdb/{imdb_id}-{s}-{e}"
        servers["10. 🛡️ Serveur 10 (VidSrc TO)"] = f"https://vidsrc.to/embed/tv/{imdb_id}/{s}/{e}"
    else:
        if tmdb_id:
            servers["1. 🇫🇷 Serveur 1 (Frembed VF)"] = f"https://frembed.pics/embed/movie/{tmdb_id}"
            servers["2. 🇫🇷 Serveur 2 (Frembed Miroir)"] = f"https://frembed.shop/api/film.php?id={tmdb_id}"

        servers["3. 🇫🇷 Serveur 3 (Smashy Audio FR)"] = f"https://embed.smashystream.com/playere.php?imdb={imdb_id}"
        servers["4. 🇫🇷 Serveur 4 (VidSrc Audio/ST FR)"] = f"https://vidsrc.me/embed/movie?imdb={imdb_id}&ds_lang=fr"

        if clean_title:
            q_enc = urllib.parse.quote(clean_title)
            servers["5. 🍿 Serveur 5 (Wiflix VF Direct)"] = f"/api/streaming/proxy?url={urllib.parse.quote('https://wiflix.voto/?s=' + q_enc)}"
            servers["6. 🎬 Serveur 6 (French-Stream VF)"] = f"/api/streaming/proxy?url={urllib.parse.quote('https://french-stream.bio/?s=' + q_enc)}"

        servers["7. 🌐 Serveur 7 (MultiEmbed Multi)"] = f"https://multiembed.mov/?video_id={imdb_id}"
        servers["8. 🍿 Serveur 8 (2Embed Cinéma)"] = f"https://www.2embed.cc/embed/{imdb_id}"
        servers["9. ⚡ Serveur 9 (AutoEmbed Rapide)"] = f"https://autoembed.to/movie/imdb/{imdb_id}"
        servers["10. 🛡️ Serveur 10 (VidSrc TO)"] = f"https://vidsrc.to/embed/movie/{imdb_id}"

    return servers

def get_trailer_url(imdb_id: str = "", title: str = "", year: str = "") -> str:
    """
    Récupère la bande-annonce officielle en HD / VF pour un film ou une série.
    Filtre strictement pour ne JAMAIS lancer de chanson ou clip musical.
    """
    if imdb_id and imdb_id.startswith('tt'):
        try:
            url = f"https://v3-cinemeta.strem.io/meta/movie/{imdb_id}.json"
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=3) as r:
                data = json.loads(r.read().decode('utf-8'))
                meta = data.get('meta', {})
                trailers = meta.get('trailerStreams', [])
                if trailers and trailers[0].get('ytId'):
                    yt = trailers[0].get('ytId')
                    return f"https://www.youtube-nocookie.com/embed/{yt}?autoplay=1&playsinline=1"
        except Exception:
            pass

    # Recherche de la vraie bande-annonce officielle en excluant musique et clips
    clean_t = urllib.parse.quote(f"{title} {year} film bande annonce vf officielle trailer cinema -musique -clip -soundtrack")
    return f"https://www.youtube-nocookie.com/embed?listType=search&list={clean_t}&autoplay=1&playsinline=1"

def get_series_stream_url(imdb_id: str, season: int = 1, episode: int = 1, server_idx: int = 1, title: str = ""):
    """Renvoie l'URL exacte d'un épisode pour le serveur sélectionné."""
    tmdb_id = get_tmdb_id(imdb_id, is_series=True)
    srv_dict = build_servers(imdb_id, tmdb_id=tmdb_id, title=title, is_series=True, season=season, episode=episode)
    keys = list(srv_dict.keys())
    idx = max(0, min(server_idx - 1, len(keys) - 1))
    return srv_dict[keys[idx]]

def search_cinemeta(query: str, limit: int = 35):
    """Recherche étendue Cinemeta (films + séries)."""
    clean_q = clean_query(query)
    if not clean_q:
        return []

    encoded = urllib.parse.quote(clean_q)
    results = {}

    # 1. Films
    try:
        url_m = f"https://v3-cinemeta.strem.io/catalog/movie/top/search={encoded}.json"
        req = urllib.request.Request(url_m, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=4) as r:
            data = json.loads(r.read().decode('utf-8'))
            for m in data.get('metas', []):
                iid = m.get('imdb_id')
                if not iid or not iid.startswith('tt'):
                    continue
                title = m.get('name', 'Film')
                # Exclure les musiques et concerts
                if MUSIC_FILTER_RE.search(title):
                    continue

                year = str(m.get('releaseInfo') or m.get('year') or '')
                poster = m.get('poster') or ""
                mid = str(m.get('moviedb_id') or '')
                if mid:
                    TMDB_CACHE[iid] = mid

                results[iid] = {
                    "id": iid,
                    "tmdb_id": mid,
                    "title": title,
                    "year": year,
                    "type": "movie",
                    "type_label": "🎬 Film Complet",
                    "is_series": False,
                    "actors": m.get('description', '')[:120] if m.get('description') else '',
                    "thumbnail": poster or "/static/icons/icon-192.png",
                    "servers": build_servers(iid, tmdb_id=mid, is_series=False),
                    "embed_url": f"https://frembed.shop/api/film.php?id={mid}" if mid else f"https://multiembed.mov/?video_id={iid}",
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
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=4) as r:
            data = json.loads(r.read().decode('utf-8'))
            for s in data.get('metas', []):
                iid = s.get('imdb_id')
                if not iid or not iid.startswith('tt') or iid in results:
                    continue
                title = s.get('name', 'Série')
                if MUSIC_FILTER_RE.search(title):
                    continue

                year = str(s.get('releaseInfo') or s.get('year') or '')
                poster = s.get('poster') or ""
                mid = str(s.get('moviedb_id') or '')
                if mid:
                    TMDB_CACHE[iid] = mid

                results[iid] = {
                    "id": iid,
                    "tmdb_id": mid,
                    "title": title,
                    "year": year,
                    "type": "serie",
                    "type_label": "📺 Série TV",
                    "is_series": True,
                    "actors": s.get('description', '')[:120] if s.get('description') else '',
                    "thumbnail": poster or "/static/icons/icon-192.png",
                    "servers": build_servers(iid, tmdb_id=mid, is_series=True),
                    "embed_url": f"https://frembed.shop/api/serie.php?id={mid}&sa=1&epi=1" if mid else f"https://multiembed.mov/?video_id={iid}&s=1&e=1",
                    "url": f"https://www.imdb.com/title/{iid}/",
                    "source": "Série Streaming (VF / VOSTFR)",
                    "duration": f"Série • {year}" if year else "Série Complète"
                }
    except Exception as e:
        print(f"[Cinemeta Série] Erreur: {e}")

    return list(results.values())

def search_imdb(query: str, limit: int = 15):
    """Recherche officielle IMDb avec filtrage strict anti-bruit et anti-musique."""
    clean_q = clean_query(query)
    if not clean_q:
        return []

    encoded = urllib.parse.quote(clean_q.lower())
    url = f"https://v3.sg.media-imdb.com/suggestion/x/{encoded}.json"
    req = urllib.request.Request(url, headers=HEADERS)

    results = []
    try:
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            items = data.get('d', [])
            for item in items:
                imdb_id = item.get('id', '')
                if not imdb_id.startswith('tt'):
                    continue

                qtype = (item.get('q') or '').lower()
                # Exclure podcasts, jeux et musiques
                if qtype in ['podcast series', 'video game', 'music video', 'soundtrack', 'music', 'song', 'album']:
                    continue

                title = item.get('l', 'Film')
                # Filtre anti-musique
                if MUSIC_FILTER_RE.search(title):
                    continue

                is_series = 'series' in qtype or 'tv' in qtype
                year = item.get('y', '')
                actors = item.get('s', '')
                
                img_data = item.get('i') or {}
                poster = img_data.get('imageUrl') or ""
                mid = TMDB_CACHE.get(imdb_id, '')
                if not mid and len(results) < 5:
                    mid = get_tmdb_id(imdb_id, is_series=is_series)

                srvs = build_servers(imdb_id, tmdb_id=mid, title=title, is_series=is_series)
                first_embed = list(srvs.values())[0] if srvs else f"https://multiembed.mov/?video_id={imdb_id}"

                results.append({
                    "id": imdb_id,
                    "tmdb_id": mid,
                    "title": title,
                    "year": str(year) if year else "",
                    "type": "serie" if is_series else "movie",
                    "type_label": "📺 Série TV" if is_series else "🎬 Film Complet",
                    "is_series": is_series,
                    "actors": actors,
                    "thumbnail": poster or "/static/icons/icon-192.png",
                    "servers": srvs,
                    "embed_url": first_embed,
                    "url": f"https://www.imdb.com/title/{imdb_id}/",
                    "source": "Cinéma Gratuit (VF / VOSTFR)",
                    "duration": f"Sortie : {year}" if year else "Film Complet"
                })
    except Exception as e:
        print(f"[IMDb] Erreur: {e}")

    return results

def get_trending_catalog(limit: int = 40):
    """
    Catalogue des films et séries les plus regardés du moment (Box-Office & Tendances).
    """
    results = {}
    try:
        url_m = "https://v3-cinemeta.strem.io/catalog/movie/top.json"
        req = urllib.request.Request(url_m, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=4) as r:
            data = json.loads(r.read().decode('utf-8'))
            for m in data.get('metas', [])[:25]:
                iid = m.get('imdb_id')
                if not iid or not iid.startswith('tt'):
                    continue
                title = m.get('name', 'Film')
                if MUSIC_FILTER_RE.search(title):
                    continue

                year = str(m.get('releaseInfo') or m.get('year') or '')
                mid = str(m.get('moviedb_id') or '')
                if mid:
                    TMDB_CACHE[iid] = mid

                results[iid] = {
                    "id": iid,
                    "tmdb_id": mid,
                    "title": title,
                    "year": year,
                    "type": "movie",
                    "type_label": "🔥 Film le Plus Regardé",
                    "is_series": False,
                    "actors": m.get('description', '')[:100] if m.get('description') else '',
                    "thumbnail": m.get('poster') or "/static/icons/icon-192.png",
                    "servers": build_servers(iid, tmdb_id=mid, is_series=False),
                    "embed_url": f"https://frembed.shop/api/film.php?id={mid}" if mid else f"https://multiembed.mov/?video_id={iid}",
                    "url": f"https://www.imdb.com/title/{iid}/",
                    "source": "Top Box-Office",
                    "duration": f"Sortie : {year}" if year else "Film Complet"
                }
    except Exception as e:
        print(f"[Trending Films] Erreur: {e}")

    try:
        url_s = "https://v3-cinemeta.strem.io/catalog/series/top.json"
        req = urllib.request.Request(url_s, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=4) as r:
            data = json.loads(r.read().decode('utf-8'))
            for s in data.get('metas', [])[:20]:
                iid = s.get('imdb_id')
                if not iid or not iid.startswith('tt') or iid in results:
                    continue
                title = s.get('name', 'Série')
                if MUSIC_FILTER_RE.search(title):
                    continue

                year = str(s.get('releaseInfo') or s.get('year') or '')
                mid = str(s.get('moviedb_id') or '')
                if mid:
                    TMDB_CACHE[iid] = mid

                results[iid] = {
                    "id": iid,
                    "tmdb_id": mid,
                    "title": title,
                    "year": year,
                    "type": "serie",
                    "type_label": "📺 Série Tendance",
                    "is_series": True,
                    "actors": s.get('description', '')[:100] if s.get('description') else '',
                    "thumbnail": s.get('poster') or "/static/icons/icon-192.png",
                    "servers": build_servers(iid, tmdb_id=mid, is_series=True),
                    "embed_url": f"https://frembed.shop/api/serie.php?id={mid}&sa=1&epi=1" if mid else f"https://multiembed.mov/?video_id={iid}&s=1&e=1",
                    "url": f"https://www.imdb.com/title/{iid}/",
                    "source": "Série Populaire",
                    "duration": f"Série • {year}" if year else "Série Complète"
                }
    except Exception as e:
        print(f"[Trending Séries] Erreur: {e}")

    return list(results.values())[:limit]

# Mappages des catégories Disney+ & sous-boutons Marvel & requêtes courantes en français
CATEGORY_QUERIES = {
    # Sous-boutons Marvel demandés par l'utilisateur
    "marvel": "Marvel",
    "marvel_avengers": "Avengers",
    "marvel_deadpool": "Deadpool",
    "marvel_xmen": "X-Men",
    "marvel_spiderman": "Spider-Man",
    "marvel_ironman": "Iron Man",
    "marvel_thor": "Thor",
    "marvel_wolverine": "Wolverine",
    "marvel_guardians": "Guardians of the Galaxy",
    "marvel_captain": "Captain America",
    
    # Styles de films Disney+ demandés par l'utilisateur
    "disney": "Disney",
    "pixar": "Pixar",
    "starwars": "Star Wars",
    "action": "Action",
    "anime": "One Piece",
    "comedie_fr": "Asterix",
    "series": "Stranger Things",

    # Traductions directes de titres de films populaires français vers l'original
    "le roi lion": "The Lion King",
    "la reine des neiges": "Frozen",
    "vice versa": "Inside Out",
    "vice-versa": "Inside Out",
    "vaiana": "Moana",
    "raiponce": "Tangled",
    "les gardiens de la galaxie": "Guardians of the Galaxy",
    "gardiens de la galaxie": "Guardians of the Galaxy",
    "le seigneur des anneaux": "Lord of the Rings",
    "pirates des caraibes": "Pirates of the Caribbean",
    "moi moche et mechant": "Despicable Me",
    "moi, moche et mechant": "Despicable Me",
    "l'age de glace": "Ice Age",
    "la belle et la bete": "Beauty and the Beast",
    "cendrillon": "Cinderella",
    "aladdin": "Aladdin",
    "mulan": "Mulan",
    "dragons": "How to Train Your Dragon",
    "intouchables": "The Intouchables",
    "amelie poulain": "Amelie",
    "le cinquieme element": "The Fifth Element"
}

def search_streaming(query: str, limit: int = 35):
    """
    Recherche universelle ultra-complète avec prise en charge des styles Disney+, Marvel et VF.
    """
    query = (query or "").strip()

    # Si la recherche est vide ou demande les films les plus regardés
    if not query or query.lower() in ["top", "tendance", "tendances", "populaire", "films", "all"]:
        return get_trending_catalog(limit=limit)

    # Si c'est un tag de catégorie Disney+ ou sous-bouton Marvel ou titre VF traduit
    clean_key = query.lower()
    if clean_key in CATEGORY_QUERIES:
        query = CATEGORY_QUERIES[clean_key]

    # Si lien direct
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
            "servers": { "Lecteur Direct": embed_url },
            "url": query,
            "source": "Lien Direct",
            "duration": "Direct"
        }]

    # 1. Recherche IMDb (très efficace pour traduire les requêtes françaises)
    imdb_results = search_imdb(query, limit=15)

    # 2. Recherche mondiale Cinemeta
    cm_results = search_cinemeta(query, limit=limit)

    merged = {}
    q_words = [w.lower() for w in clean_query(query).split() if len(w) > 1]

    # On ajoute d'abord les résultats IMDb (qui comprennent les titres traduits)
    for item in imdb_results:
        iid = item.get('id')
        if iid and iid not in merged:
            merged[iid] = item

    # Puis on ajoute les résultats Cinemeta pertinents
    for item in cm_results:
        iid = item.get('id')
        if not iid or iid in merged:
            continue
        title_lower = item.get('title', '').lower()
        if q_words and not any(w in title_lower for w in q_words):
            continue
        merged[iid] = item

    # Tri par pertinence exacte
    def sort_score(item):
        t = item.get('title', '').lower()
        clean_user_q = clean_query(query).lower()
        if t == clean_user_q:
            return 100
        if t.startswith(clean_user_q):
            return 80
        if clean_user_q in t:
            return 60
        common = sum(1 for w in q_words if w in t)
        return common * 10

    sorted_list = sorted(list(merged.values()), key=sort_score, reverse=True)
    if not sorted_list:
        sorted_list = list(merged.values()) or imdb_results or cm_results

    return sorted_list[:limit]

def build_site_search_url(site_url: str, query: str) -> str:
    """
    Construit l'URL de recherche exacte pour n'importe quel site personnalisé.
    Gère tous les sites de streaming, films, séries, animés et plateformes vidéo (Wiflix, French-Stream, etc.)
    """
    if not site_url:
        return ""
    if not site_url.startswith(('http://', 'https://')):
        site_url = 'https://' + site_url

    parsed = urllib.parse.urlparse(site_url)
    domain = parsed.netloc.lower()
    q_enc = urllib.parse.quote(query)

    # Sites spécifiques avec formats de recherche dédiés
    if 'xvideos' in domain:
        return f"{parsed.scheme}://{parsed.netloc}/?k={q_enc}"
    elif 'pornhub' in domain:
        return f"{parsed.scheme}://{parsed.netloc}/video/search?search={q_enc}"
    elif 'xhamster' in domain:
        return f"{parsed.scheme}://{parsed.netloc}/search/{q_enc}"
    elif 'spankbang' in domain:
        return f"{parsed.scheme}://{parsed.netloc}/s/{q_enc}/"
    elif 'youporn' in domain:
        return f"{parsed.scheme}://{parsed.netloc}/search/?query={q_enc}"
    elif 'redtube' in domain:
        return f"{parsed.scheme}://{parsed.netloc}/?search={q_enc}"
    elif 'wiflix' in domain:
        return f"{parsed.scheme}://{parsed.netloc}/?s={q_enc}"
    elif 'french-stream' in domain:
        return f"{parsed.scheme}://{parsed.netloc}/?s={q_enc}"
    elif 'darkino' in domain:
        return f"{parsed.scheme}://{parsed.netloc}/recherche?q={q_enc}"
    elif 'youtube' in domain:
        return f"https://www.youtube.com/results?search_query={q_enc}"
    elif 'dailymotion' in domain:
        return f"https://www.dailymotion.com/search/{q_enc}"

    # Format universel compatible 95% du web
    return f"{parsed.scheme}://{parsed.netloc}/?s={q_enc}"

def scrape_site_results(search_url: str, base_url: str) -> list:
    """
    Extrait les vidéos, films ou articles trouvés sur la page de recherche d'un site personnalisé.
    """
    items = []
    try:
        req = urllib.request.Request(
            search_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8'
            }
        )
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        links = re.findall(r'<a\s+[^>]*href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE)
        seen_urls = set()

        for href, inner in links:
            if not href or href in ['#', '/', 'javascript:void(0)'] or href in seen_urls:
                continue
            full_url = urllib.parse.urljoin(base_url, href)
            clean_text = re.sub(r'<[^>]+>', ' ', inner).strip()
            img_match = re.search(r'<img\s+[^>]*src=[\'"]([^\'"]+)[\'"]', inner, re.IGNORECASE)

            # Ne retenir que les éléments ayant du sens (avec image ou texte pertinent)
            if (img_match or len(clean_text) >= 5) and len(clean_text) < 120:
                if any(ext in full_url.lower() for ext in ['.png', '.jpg', '.jpeg', '.svg', '.css', '.js', '/tag/', '/category/']):
                    continue
                seen_urls.add(href)
                img_url = urllib.parse.urljoin(base_url, img_match.group(1)) if img_match else ""
                items.append({
                    "title": clean_text or "Vidéo trouvée",
                    "url": full_url,
                    "embed_url": f"/api/streaming/proxy?url={urllib.parse.quote(full_url)}",
                    "thumbnail": img_url or "/static/icons/icon-192.png",
                    "source": urllib.parse.urlparse(base_url).netloc
                })
                if len(items) >= 24:
                    break
    except Exception as e:
        print(f"[scrape_site_results] {e}")

    return items
