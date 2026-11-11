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
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, abort, redirect, url_for

from config import load_config, save_config, DEFAULT_CONFIG
from music_tagger import sanitize_filename
import downloader
from downloader import (
    search_tracks,
    download_track_async,
    download_theme_async,
    download_singer_discography_async,
    get_library,
    delete_track,
    update_track_tags_and_move,
    ACTIVE_DOWNLOADS
)
import scanner
import themes
import qrcode

app = Flask(__name__, template_folder='templates', static_folder='static')

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
# API THÈMES & AMBIANCES
# =====================================================================

@app.route('/api/themes')
def api_themes():
    return jsonify(themes.get_all_themes())

@app.route('/api/theme/<theme_id>')
def api_theme(theme_id):
    theme = themes.get_theme_by_id(theme_id)
    if not theme:
        return jsonify({"error": "Thème introuvable"}), 404
    return jsonify(theme)

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

@app.route('/api/cloud/reset', methods=['GET', 'POST'])
def api_cloud_reset():
    """Préserve la bibliothèque locale (neutralisé pour sécurité)."""
    return jsonify({
        "success": True,
        "message": "Stockage local préservé. Vos musiques restent en sécurité sur votre appareil."
    })

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
    response = send_file(
        filepath,
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
