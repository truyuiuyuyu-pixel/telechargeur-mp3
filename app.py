# -*- coding: utf-8 -*-
"""
app.py — Serveur principal Téléchargeur MP3 HD (Téléphone & Ordinateur)
Prise en charge universelle :
- Tous les sites de musique (YouTube, SoundCloud, Bandcamp, TikTok, MP3 direct...)
- Mode Thèmes complet (Amour, Halloween, Noël, Soirée, Sport, Chill...)
- Téléchargement physique direct sur le téléphone (sans cloud intermédiaire)
- Dossiers par chanteur avec tags ID3 officiels
- Interface responsive PC et interface mobile dédiée PWA
"""

import os
import io
import socket
import webbrowser
import threading
import json
import time
import zipfile
import requests
import urllib.request
import urllib.parse
import re
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, abort, redirect, url_for, make_response, Response

from config import load_config, save_config, DEFAULT_CONFIG
from music_tagger import sanitize_filename
import downloader
from downloader import (
    search_tracks,
    download_track_async,
    download_theme_async,
    download_singer_discography_async,
    search_videos,
    download_video_async,
    get_library,
    delete_track,
    update_track_tags_and_move,
    ACTIVE_DOWNLOADS
)
import scanner
import themes
import streaming
import qrcode
from temp_cleaner import reset_temp_storage, auto_clean_old_temp_files
from downloader import download_single_track_sync

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
try:
    app.json.sort_keys = False
except Exception:
    app.config['JSON_SORT_KEYS'] = False

@app.after_request
def add_no_cache_headers(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

def _start_server_cleanup_daemon():
    def _loop():
        while True:
            time.sleep(3600)  # Vérifie toutes les heures
            auto_clean_old_temp_files()
    threading.Thread(target=_loop, daemon=True).start()

_start_server_cleanup_daemon()

def get_local_ip():
    """Détecte l'adresse IP locale de la machine sur le réseau WiFi/LAN."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def is_mobile_request():
    """Détecte si la requête provient d'un smartphone ou tablette."""
    ua = request.headers.get('User-Agent', '').lower()
    mobile_keywords = ['android', 'iphone', 'ipad', 'ipod', 'mobile', 'blackberry', 'windows phone']
    return any(kw in ua for kw in mobile_keywords)

PORT = int(os.environ.get("PORT", 5000))

# =====================================================================
# ROUTES PAGES WEB
# =====================================================================

@app.route('/')
def index():
    """Page d'accueil : redirige automatiquement les téléphones vers l'interface mobile."""
    if is_mobile_request() and request.args.get('desktop') != '1':
        return redirect(url_for('mobile_app'))
    return render_template('index.html')

@app.route('/mobile')
def mobile_app():
    """Interface mobile optimisée pour smartphone (PWA & tactile)."""
    return render_template('mobile.html')

@app.route('/telecharger-app')
@app.route('/installer')
@app.route('/app')
def download_app_page():
    """Page de téléchargement et installation pour mobile."""
    return render_template('download_app.html')

@app.route('/api/download-apk')
@app.route('/download-apk')
def download_apk():
    """Téléchargement direct du fichier APK Android."""
    apk_path = os.path.join(app.static_folder, 'Telechargeur_MP3_HD.apk')
    if not os.path.exists(apk_path):
        return abort(404)
    response = send_file(
        apk_path,
        mimetype='application/vnd.android.package-archive',
        as_attachment=True,
        download_name='Telechargeur_MP3_HD.apk'
    )
    response.headers['Content-Disposition'] = 'attachment; filename="Telechargeur_MP3_HD.apk"'
    response.headers['Cache-Control'] = 'no-cache'
    return response

@app.route('/static/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript', max_age=0)

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')

@app.route('/api/network-info')
def network_info():
    ip = get_local_ip()
    return jsonify({
        "local_ip": ip,
        "port": PORT,
        "mobile_url": f"http://{ip}:{PORT}",
        "local_url": f"http://localhost:{PORT}"
    })

@app.route('/api/qr')
def qr_code():
    """QR Code pour connexion instantanée du téléphone sur le réseau WiFi."""
    ip = get_local_ip()
    target_url = f"http://{ip}:{PORT}"
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(target_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1e293b", back_color="#ffffff")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

# =====================================================================
# API CONFIGURATION
# =====================================================================

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'POST':
        data = request.json or {}
        current_cfg = load_config()
        for key in ["mp3_site", "mp3_site_url", "search_site", "search_site_url", "music_folder", "create_artist_folder", "audio_quality"]:
            if key in data:
                current_cfg[key] = data[key]
        current_cfg["configured"] = True
        save_config(current_cfg)
        return jsonify({"success": True, "config": current_cfg})
    else:
        return jsonify(load_config())

# =====================================================================
# API RECHERCHE MULTI-SOURCES
# =====================================================================

@app.route('/api/search')
def search():
    query = request.args.get('q', '').strip()
    source = request.args.get('source', 'all').lower()
    if not query:
        return jsonify({"results": [], "theme": None})

    theme_info = themes.match_theme_by_query(query)
    results = search_tracks(query, limit=12, source=source)

    return jsonify({
        "results": results,
        "theme": {
            "id": theme_info["id"],
            "name": theme_info["name"],
            "badge": theme_info["badge"],
            "icon": theme_info["icon"],
            "description": theme_info["description"],
            "tracks": theme_info.get("tracks", [])
        } if theme_info else None
    })

# =====================================================================
# API VIDÉO & STREAMING (MP4 HD & LECTURE DIRECTE)
# =====================================================================

@app.route('/api/video/search')
def api_video_search():
    """Recherche des vidéos / films / clips sur les plateformes vidéo gratuites."""
    q = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 15))
    if not q:
        return jsonify([])
    results = search_videos(q, limit=limit)
    return jsonify(results)

@app.route('/api/video/download', methods=['POST'])
def api_video_download():
    """Télécharge une vidéo complète en MP4 HD en tâche de fond."""
    data = request.json or {}
    url = data.get('url', '').strip()
    title = data.get('title', '').strip()
    if not url:
        return jsonify({"error": "URL manquante"}), 400
    task_id = download_video_async(url, title=title)
    return jsonify({"task_id": task_id, "status": "started"})

@app.route('/api/video/info')
def api_video_info():
    """Récupère les détails et l'URL de streaming direct d'une vidéo."""
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({"error": "URL manquante"}), 400
    res = search_videos(url, limit=1)
    if res:
        return jsonify(res[0])
    return jsonify({"error": "Vidéo introuvable"}), 404

@app.route('/api/streaming/search')
def api_streaming_search():
    """Recherche des VRAIS films et séries en streaming gratuit multi-serveurs (VF/VOSTFR)."""
    q = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 35))
    results = streaming.search_streaming(q, limit=limit)
    return jsonify(results)

@app.route('/api/streaming/servers')
def api_streaming_servers():
    """Génère la liste complète des serveurs pour un film ou une série avec résolution VF instantanée."""
    imdb_id = request.args.get('id', '').strip()
    mtype = request.args.get('type', 'movie').strip()
    is_series = mtype in ['series', 'serie', 'tv']
    season = int(request.args.get('season', 1))
    episode = int(request.args.get('episode', 1))

    if not imdb_id:
        return jsonify({"error": "Identifiant manquant"}), 400

    tmdb_id = streaming.get_tmdb_id(imdb_id, is_series=is_series)
    servers = streaming.build_servers(imdb_id, tmdb_id=tmdb_id, is_series=is_series, season=season, episode=episode)
    return jsonify({"id": imdb_id, "tmdb_id": tmdb_id, "servers": servers})

@app.route('/api/streaming/episode')
def api_streaming_episode():
    """Génère l'URL d'un épisode spécifique d'une série pour un serveur donné."""
    imdb_id = request.args.get('id', '').strip()
    season = int(request.args.get('season', 1))
    episode = int(request.args.get('episode', 1))
    server = int(request.args.get('server', 1))
    if not imdb_id:
        return jsonify({"error": "Identifiant manquant"}), 400
    embed_url = streaming.get_series_stream_url(imdb_id, season=season, episode=episode, server_idx=server)
    return jsonify({"embed_url": embed_url})

@app.route('/api/streaming/trailer')
def api_streaming_trailer():
    """Renvoie l'URL de la bande-annonce officielle en VF/HD pour un film ou une série."""
    imdb_id = request.args.get('id', '').strip()
    title = request.args.get('title', '').strip()
    year = request.args.get('year', '').strip()
    trailer_url = streaming.get_trailer_url(imdb_id, title=title, year=year)
    return jsonify({"trailer_url": trailer_url, "title": title, "year": year})

@app.route('/api/streaming/proxy')
def api_streaming_proxy():
    """
    Proxy débloqueur universel : permet d'intégrer N'IMPORTE QUEL site dans le lecteur iframe,
    y compris les sites avec X-Frame-Options (sites de streaming, sites -18, etc.).
    Supprime les en-têtes bloquants et injecte <base href="..."> pour charger images/scripts.
    """
    target_url = request.args.get('url', '').strip()
    if not target_url:
        return "URL manquante", 400

    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url

    try:
        req = urllib.request.Request(
            target_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none'
            }
        )
        with urllib.request.urlopen(req, context=streaming.SSL_CTX, timeout=10) as resp:
            content_type = resp.headers.get('Content-Type', 'text/html')
            data = resp.read()

            if 'text/html' in content_type:
                try:
                    html_text = data.decode('utf-8')
                except Exception:
                    html_text = data.decode('latin-1', errors='ignore')

                parsed = urllib.parse.urlparse(target_url)
                base_href = f"{parsed.scheme}://{parsed.netloc}/"
                base_tag = f'<base href="{base_href}">'

                # Désactiver les framebusters JS si présents
                html_text = re.sub(r'top\.location\s*!=\s*self\.location', 'false', html_text)
                html_text = re.sub(r'top\.location\.href\s*=', 'console.log(', html_text)

                if re.search(r'<head[^>]*>', html_text, re.IGNORECASE):
                    html_text = re.sub(r'(<head[^>]*>)', r'\1' + base_tag, html_text, count=1, flags=re.IGNORECASE)
                else:
                    html_text = base_tag + html_text

                response = make_response(html_text)
                response.headers['Content-Type'] = content_type
                response.headers.pop('X-Frame-Options', None)
                response.headers.pop('Content-Security-Policy', None)
                response.headers['Access-Control-Allow-Origin'] = '*'
                return response
            else:
                response = make_response(data)
                response.headers['Content-Type'] = content_type
                response.headers.pop('X-Frame-Options', None)
                response.headers.pop('Content-Security-Policy', None)
                response.headers['Access-Control-Allow-Origin'] = '*'
                return response

    except Exception as e:
        parsed = urllib.parse.urlparse(target_url)
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>{parsed.netloc}</title>
        <style>body{{font-family:sans-serif;background:#0f172a;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;text-align:center;padding:20px;}}</style>
        </head>
        <body>
            <div>
                <h2>🔒 Protection de sécurité externe détectée</h2>
                <p>Le site <b>{parsed.netloc}</b> nécessite une ouverture directe :</p>
                <a href="{target_url}" target="_blank" rel="noopener" style="display:inline-block;padding:12px 24px;background:#10b981;color:#fff;text-decoration:none;border-radius:10px;font-weight:bold;margin-top:10px;">
                    🌐 Ouvrir {parsed.netloc} dans un nouvel onglet
                </a>
            </div>
        </body>
        </html>
        """, 200

@app.route('/api/streaming/search_site')
def api_streaming_search_site():
    """
    Recherche directement dans le site manuel donné par l'utilisateur.
    Construit l'URL de recherche dédiée et tente d'extraire les vidéos du site.
    """
    site_url = request.args.get('site', '').strip()
    query = request.args.get('q', '').strip()
    if not site_url or not query:
        return jsonify({"error": "Paramètres 'site' et 'q' requis"}), 400

    search_url = streaming.build_site_search_url(site_url, query)
    proxy_url = f"/api/streaming/proxy?url={urllib.parse.quote(search_url)}"
    results = streaming.scrape_site_results(search_url, site_url)

    return jsonify({
        "site_url": site_url,
        "query": query,
        "search_url": search_url,
        "proxy_url": proxy_url,
        "results": results
    })

# =====================================================================
# API THÈMES & AMBIANCES
# =====================================================================

@app.route('/api/themes')
def api_themes():
    q = request.args.get('q', '').strip()
    if q:
        return jsonify(themes.search_themes_catalog(q))
    return jsonify(themes.get_all_themes())

@app.route('/api/themes/dynamic')
def api_themes_dynamic():
    """
    Recherche ou création dynamique d'un thème complet sur le web.
    Permet à l'utilisateur de chercher n'importe quel univers (ex: Iron Man, Spider-Man, Star Wars, Batman, Zelda...)
    et de recevoir automatiquement une sélection complète et riche de plus de 30 musiques de ce thème !
    """
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"error": "Requête vide"}), 400
    
    # 1. Vérifier si un thème existant correspond
    theme_match = themes.match_theme_by_query(query)
    
    # 2. Effectuer des requêtes multiples pour trouver des dizaines de morceaux variés
    queries = [
        f"{query} theme song official soundtrack",
        f"{query} ost music original",
        f"{query} best tracks full album"
    ]
    seen_ids = set()
    web_results = []
    
    for q_item in queries:
        try:
            res = downloader.search_tracks(q_item, source='all', limit=15)
            for r in res:
                uid = r.get("id") or r.get("url") or f"{r.get('artist')}_{r.get('title')}".lower()
                if uid and uid not in seen_ids:
                    seen_ids.add(uid)
                    web_results.append(r)
        except Exception as e:
            print(f"Erreur recherche query dynamic '{q_item}': {e}")

    combined_tracks = []
    if theme_match and theme_match.get("tracks"):
        for t in theme_match.get("tracks"):
            combined_tracks.append({
                "title": t.get("title"),
                "artist": t.get("artist"),
                "query": t.get("query"),
                "url": t.get("url"),
                "thumbnail": t.get("thumbnail")
            })
            
    for r in web_results:
        tit = r.get("title") or r.get("raw_title") or "Titre"
        if not any(tit.lower() in (ct.get("title") or "").lower() for ct in combined_tracks):
            combined_tracks.append({
                "title": tit,
                "artist": r.get("artist") or query.title(),
                "query": f"{r.get('artist', '')} {r.get('title', '')}".strip() or r.get("url"),
                "url": r.get("url"),
                "thumbnail": r.get("thumbnail")
            })

    dyn_id = "dyn_" + sanitize_filename(query).lower()[:20]
    icon = theme_match.get("icon", "fa-film") if theme_match else "fa-film"
    color = theme_match.get("color", "#6366f1") if theme_match else "#6366f1"
    
    dynamic_theme = {
        "id": dyn_id,
        "name": (theme_match.get("name") if theme_match else query.title()),
        "icon": icon,
        "color": color,
        "badge": f"🎬 Thème {query.title()}",
        "description": f"Sélection enrichie de {len(combined_tracks)} musiques cultes pour l'univers {query.title()}",
        "tracks": combined_tracks,
        "track_count": len(combined_tracks)
    }
    themes.DYNAMIC_THEMES[dyn_id] = dynamic_theme
    return jsonify(dynamic_theme)

@app.route('/api/theme/<theme_id>')
def api_theme(theme_id):
    theme = themes.get_theme_by_id(theme_id)
    if not theme:
        return jsonify({"error": "Thème introuvable"}), 404
    return jsonify(theme)

@app.route('/api/theme/<theme_id>/search')
def api_theme_search(theme_id):
    """
    Recherche en ligne des musiques spécifiques dans le cadre d'un thème musical.
    Permet de trouver une infinité de musiques pour n'importe quel thème.
    """
    theme = themes.get_theme_by_id(theme_id)
    if not theme:
        return jsonify({"error": "Thème introuvable"}), 404

    q = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 30))
    theme_name = theme.get("name", "")
    keywords = theme.get("keywords", [])
    main_keyword = keywords[0] if keywords else theme_name

    if q:
        query = f"{main_keyword} {q}"
    else:
        query = f"{theme_name} music"

    results = search_tracks(query=query, limit=limit, source="all")
    return jsonify({
        "theme_id": theme_id,
        "theme_name": theme_name,
        "query": q,
        "results": results
    })

@app.route('/api/preview-track')
def api_preview_track():
    """
    Renvoie une URL d'extrait audio de 30 secondes pour écouter un bout de la musique
    avant de la télécharger. Utilise Deezer puis iTunes en cascade ultra-rapide.
    """
    artist = request.args.get('artist', '').strip()
    title = request.args.get('title', '').strip()
    q = request.args.get('q', '').strip()

    search_term = f"{artist} {title}".strip() or q
    if not search_term:
        return jsonify({"error": "Terme de recherche manquant"}), 400

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    # 1. Tentative Deezer (MP3 officiel 30s haute fidélité)
    try:
        r = requests.get('https://api.deezer.com/search', params={'q': search_term, 'limit': 1}, headers=headers, timeout=4).json()
        if r.get('data') and len(r['data']) > 0:
            track_data = r['data'][0]
            preview = track_data.get('preview')
            if preview:
                return jsonify({
                    "preview_url": preview,
                    "title": track_data.get('title') or title,
                    "artist": (track_data.get('artist') or {}).get('name') or artist,
                    "cover": (track_data.get('album') or {}).get('cover_medium'),
                    "duration": 30,
                    "source": "Deezer HD"
                })
    except Exception as e:
        pass

    # 2. Tentative iTunes / Apple Music (AAC/M4A officiel 30s)
    try:
        r = requests.get('https://itunes.apple.com/search', params={'term': search_term, 'limit': 1, 'media': 'music'}, headers=headers, timeout=4).json()
        if r.get('results') and len(r['results']) > 0:
            item = r['results'][0]
            preview = item.get('previewUrl')
            if preview:
                return jsonify({
                    "preview_url": preview,
                    "title": item.get('trackName') or title,
                    "artist": item.get('artistName') or artist,
                    "cover": item.get('artworkUrl100'),
                    "duration": 30,
                    "source": "Apple Music"
                })
    except Exception as e:
        pass

    return jsonify({"error": "Aucun extrait disponible pour ce morceau"}), 404

@app.route('/api/theme/<theme_id>/download-all', methods=['POST'])
def api_theme_download_all(theme_id):
    """Télécharge l'ensemble des titres d'un thème musical complet."""
    try:
        task_id = download_theme_async(theme_id)
        return jsonify({"task_id": task_id, "status": "started"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/theme/<theme_id>/download-zip')
def api_theme_download_zip(theme_id):
    """Télécharge toutes les musiques disponibles de ce thème sous forme d'un fichier ZIP."""
    theme = themes.get_theme_by_id(theme_id)
    if not theme:
        return abort(404)

    cfg = load_config()
    music_base = cfg.get("music_folder", "Musique")
    theme_tracks = theme.get("tracks", [])

    memory_file = io.BytesIO()
    found_count = 0

    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for t in theme_tracks:
            t_art = sanitize_filename(t.get("artist", ""))
            t_tit = sanitize_filename(t.get("title", ""))
            # Chercher dans Musique/Artiste/Titre.mp3
            art_dir = os.path.join(music_base, t_art)
            if os.path.exists(art_dir):
                for f in os.listdir(art_dir):
                    if f.lower().endswith(".mp3") and t_tit.lower() in f.lower():
                        fp = os.path.join(art_dir, f)
                        zf.write(fp, f"{t_art}/{f}")
                        found_count += 1
                        break

    if found_count == 0:
        return jsonify({"error": "Aucune musique de ce thème n'a encore été téléchargée. Lancez le téléchargement du thème d'abord.", "empty": True}), 200

    memory_file.seek(0)
    zip_name = f"Theme_{theme_id.capitalize()}_MP3_HD.zip"
    return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name=zip_name)

# =====================================================================
# API TÉLÉCHARGEMENT & FICHIERS
# =====================================================================

@app.route('/api/clean-temp', methods=['GET', 'POST'])
@app.route('/api/cloud/reset', methods=['GET', 'POST'])
def api_clean_temp():
    """Libère l'espace temporaire du serveur pour éviter la saturation du disque."""
    res = reset_temp_storage()
    return jsonify(res)

@app.route('/api/direct-download')
def api_direct_download():
    """
    Téléchargement 100% direct dans la mémoire du smartphone ou PC.
    Le navigateur du téléphone reçoit directement le fichier audio MP3 HD 320k
    en pièce jointe sans passer par un cloud.
    """
    url = request.args.get('url', '').strip()
    q = request.args.get('q', '').strip()
    artist = request.args.get('artist', '').strip()
    title = request.args.get('title', '').strip()

    target = url or q
    if not target:
        return abort(400, "Aucun lien ou titre fourni")

    try:
        target_path, filename = download_single_track_sync(
            url=target,
            chosen_artist=artist,
            chosen_title=title
        )
        if not target_path or not os.path.exists(target_path):
            return abort(500, "Erreur génération fichier MP3")

        response = send_file(
            target_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=filename
        )
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Type'] = 'audio/mpeg'
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download', methods=['POST'])
def start_download():
    data = request.json or {}
    url = data.get('url')
    artist = data.get('artist', '').strip()
    title = data.get('title', '').strip()
    album = data.get('album', '').strip()
    cover_url = data.get('cover_url')

    if not url:
        return jsonify({"error": "URL ou terme manquant"}), 400

    task_id = download_track_async(
        url=url,
        chosen_artist=artist,
        chosen_title=title,
        album=album,
        cover_url=cover_url
    )
    return jsonify({"task_id": task_id, "status": "started"})

@app.route('/api/download-status/<task_id>')
def download_status(task_id):
    if task_id in ACTIVE_DOWNLOADS:
        return jsonify(ACTIVE_DOWNLOADS[task_id])
    return jsonify({"status": "not_found"}), 404

@app.route('/api/download-ready/<task_id>')
def download_ready(task_id):
    """
    Téléchargement direct du fichier MP3 HD 320k vers la mémoire du téléphone ou PC.
    NE SUPPRIME JAMAIS LE FICHIER (garantit la persistance sur l'appareil).
    """
    if task_id not in ACTIVE_DOWNLOADS:
        return abort(404)

    info = ACTIVE_DOWNLOADS[task_id]
    if info.get("status") != "completed":
        return jsonify({"status": info.get("status"), "ready": False}), 202

    filepath = info.get("filepath")
    if not filepath or not os.path.exists(filepath):
        return abort(404)

    filename = os.path.basename(filepath)
    is_video = filename.lower().endswith(('.mp4', '.mkv', '.webm', '.avi', '.mov'))
    mimetype = 'video/mp4' if is_video else 'audio/mpeg'
    response = send_file(
        filepath,
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename
    )
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Type'] = mimetype
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/api/download-file/<path:rel_path>')
def download_file(rel_path):
    """Téléchargement direct d'un MP3 spécifique de la bibliothèque sur le smartphone."""
    cfg = load_config()
    music_base = cfg.get("music_folder", "Musique")
    full_path = os.path.normpath(os.path.join(music_base, rel_path))

    if not full_path.startswith(os.path.normpath(music_base)) or not os.path.exists(full_path):
        return abort(404)

    filename = os.path.basename(full_path)
    response = send_file(
        full_path,
        mimetype='audio/mpeg',
        as_attachment=True,
        download_name=filename
    )
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Type'] = 'audio/mpeg'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/api/download-all-to-phone')
def download_all_to_phone():
    """
    Télécharge TOUTES les musiques en un seul fichier ZIP directement
    dans le dossier Téléchargements du smartphone.
    """
    cfg = load_config()
    music_base = cfg.get("music_folder", "Musique")
    if not os.path.isabs(music_base):
        music_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), music_base)

    if not os.path.exists(music_base):
        return abort(404)

    memory_file = io.BytesIO()
    file_count = 0
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(music_base):
            for file in files:
                if file.lower().endswith(('.mp3', '.m4a', '.flac', '.wav', '.ogg')):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, music_base)
                    zf.write(file_path, arcname)
                    file_count += 1

    if file_count == 0:
        return jsonify({"error": "Aucune musique trouvée à télécharger", "empty": True}), 200

    memory_file.seek(0)
    zip_filename = "Mes_Musiques_MP3_HD.zip"

    response = send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_filename
    )
    response.headers['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/api/library')
def library():
    lib = get_library()
    return jsonify(lib)

@app.route('/api/stream/<path:rel_path>')
def stream_music(rel_path):
    """Lecture audio en streaming directement dans le lecteur web/mobile."""
    cfg = load_config()
    music_base = cfg.get("music_folder", "Musique")
    full_path = os.path.normpath(os.path.join(music_base, rel_path))

    if not full_path.startswith(os.path.normpath(music_base)) or not os.path.exists(full_path):
        return abort(404)

    return send_file(full_path, mimetype='audio/mpeg')

@app.route('/api/track', methods=['DELETE'])
def remove_track():
    rel_path = request.args.get('path')
    if not rel_path:
        return jsonify({"error": "Chemin manquant"}), 400
    try:
        deleted = delete_track(rel_path)
        return jsonify({"success": deleted})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/retag', methods=['POST'])
def retag():
    data = request.json or {}
    rel_path = data.get('path')
    artist = data.get('artist')
    title = data.get('title')
    album = data.get('album')
    try:
        new_rel = update_track_tags_and_move(rel_path, artist, title, album)
        return jsonify({"success": True, "new_path": new_rel})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# =====================================================================
# API MODE CHANTEUR COMPLET & SCANNER
# =====================================================================

@app.route('/api/singer/discography')
def singer_discography():
    artist = request.args.get('artist', '').strip()
    if not artist:
        return jsonify({"error": "Nom d'artiste manquant"}), 400
    limit = int(request.args.get('limit', 50))
    data = scanner.search_singer_discography(artist, limit=limit)
    return jsonify(data)

@app.route('/api/singer/verify-folder')
def singer_verify_folder():
    artist = request.args.get('artist', '').strip()
    if not artist:
        return jsonify({"error": "Nom d'artiste manquant"}), 400
    report = scanner.scan_and_verify_singer_folder(artist)
    return jsonify(report)

@app.route('/api/singer/verify-track')
def singer_verify_track():
    title = request.args.get('title', '').strip()
    artist = request.args.get('artist', '').strip()
    target = request.args.get('target', '').strip()
    if not title or not target:
        return jsonify({"error": "Paramètres manquants"}), 400
    res = scanner.verify_track_artist(title, artist, target)
    return jsonify(res)

@app.route('/api/singer/create-files', methods=['POST'])
def singer_create_files():
    data = request.json or {}
    artist = data.get('artist', '').strip()
    tracks = data.get('tracks', [])
    if not artist:
        return jsonify({"error": "Nom d'artiste manquant"}), 400
    res = scanner.create_artist_files_and_playlist(artist, tracks)
    return jsonify({"success": True, "files": res})

@app.route('/api/singer/download-all', methods=['POST'])
def singer_download_all():
    data = request.json or {}
    artist = data.get('artist', '').strip()
    tracks = data.get('tracks', [])
    skip_duplicates = data.get('skip_duplicates', False)

    if not artist or not tracks:
        return jsonify({"error": "Données incomplètes"}), 400

    task_id = download_singer_discography_async(
        artist_name=artist,
        tracks=tracks,
        skip_duplicates=skip_duplicates
    )
    return jsonify({"task_id": task_id, "status": "started"})

@app.route('/api/singer/download-zip/<path:artist_name>')
def download_artist_zip(artist_name):
    cfg = load_config()
    music_base = cfg.get("music_folder", "Musique")
    clean_artist = sanitize_filename(artist_name)
    artist_dir = os.path.normpath(os.path.join(music_base, clean_artist))

    if not os.path.exists(artist_dir):
        return abort(404)

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(artist_dir):
            for file in files:
                if file.lower().endswith(('.mp3', '.m3u8', '.txt', '.json')):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(artist_dir))
                    zf.write(file_path, arcname)

    memory_file.seek(0)
    zip_filename = f"{clean_artist}_MP3_HD_320k.zip"
    return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name=zip_filename)

@app.route('/api/phone/register-music', methods=['POST'])
def phone_register_music():
    data = request.json or {}
    tracks = data.get('tracks', [])
    count = scanner.register_phone_music(tracks)
    return jsonify({"success": True, "registered_count": count})

@app.route('/api/scanner/summary')
def scanner_summary():
    existing = scanner.scan_all_existing_music()
    return jsonify({
        "total_existing": len(existing),
        "pc_count": len([x for x in existing if "PC" in x.get("source", "") or "App" in x.get("source", "")]),
        "phone_count": len([x for x in existing if "Téléphone" in x.get("source", "")])
    })

# =====================================================================
# DÉMARRAGE DU SERVEUR
# =====================================================================

if __name__ == '__main__':
    ip = get_local_ip()
    sep = "=" * 65
    print(sep)
    print(" 🎵 APPLICATION TÉLÉCHARGEUR MP3 POUR TÉLÉPHONE ET ORDINATEUR 🎵")
    print(sep)
    print(f" PC        : http://localhost:{PORT}")
    print(f" Téléphone : http://{ip}:{PORT}")
    print(sep)
    print(" Scannez le QR Code dans l'interface pour l'utiliser sur smartphone !")
    print(" Vos musiques sont sauvegardées directement sur vos appareils.")
    print(sep)

    def open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open(f"http://localhost:{PORT}")
        except Exception:
            pass

    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT, debug=False)
