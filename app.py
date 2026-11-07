import os
import io
import socket
import webbrowser
import threading
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, abort, redirect, url_for

from config import load_config, save_config, DEFAULT_CONFIG
from music_tagger import sanitize_filename
import downloader
from downloader import (
    search_tracks,
    download_track_async,
    download_singer_discography_async,
    get_library,
    delete_track,
    update_track_tags_and_move,
    ACTIVE_DOWNLOADS
)
import scanner
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
    """Détecte si la requête vient d'un appareil mobile."""
    ua = request.headers.get('User-Agent', '').lower()
    mobile_keywords = ['android', 'iphone', 'ipad', 'ipod', 'mobile', 'blackberry', 'windows phone']
    return any(kw in ua for kw in mobile_keywords)

PORT = int(os.environ.get("PORT", 5000))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mobile')
def mobile_app():
    """Interface mobile optimisée PWA — s'installe sur l'écran d'accueil."""
    return render_template('mobile.html')

@app.route('/telecharger-app')
@app.route('/installer')
@app.route('/app')
def download_app_page():
    """Page de téléchargement/installation de l'application mobile (APK Android natif + web)."""
    return render_template('download_app.html')

@app.route('/api/download-apk')
@app.route('/download-apk')
def download_apk():
    """Téléchargement direct du fichier APK Android natif."""
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
    response.headers['Content-Type'] = 'application/vnd.android.package-archive'
    response.headers['Cache-Control'] = 'no-cache'
    return response

@app.route('/static/sw.js')
def service_worker():
    """Sert le Service Worker depuis la racine (scope obligatoire pour le SW)."""
    return send_from_directory('static', 'sw.js',
                               mimetype='application/javascript',
                               max_age=0)

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
    """Génère l'image du QR Code pour scanner et ouvrir directement l'application sur smartphone."""
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

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'POST':
        data = request.json or {}
        current_cfg = load_config()
        # Mettre à jour avec les champs reçus
        for key in ["mp3_site", "mp3_site_url", "search_site", "search_site_url", "music_folder", "create_artist_folder", "audio_quality"]:
            if key in data:
                current_cfg[key] = data[key]
        current_cfg["configured"] = True
        save_config(current_cfg)
        return jsonify({"success": True, "config": current_cfg})
    else:
        return jsonify(load_config())

@app.route('/api/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"results": []})
    results = search_tracks(query, limit=12)
    return jsonify({"results": results})

@app.route('/api/download', methods=['POST'])
def start_download():
    data = request.json or {}
    url = data.get('url')
    artist = data.get('artist', '').strip()
    title = data.get('title', '').strip()
    album = data.get('album', '').strip()
    cover_url = data.get('cover_url')

    if not url:
        return jsonify({"error": "URL manquante"}), 400

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

@app.route('/api/library')
def library():
    lib = get_library()
    return jsonify(lib)

@app.route('/api/stream/<path:rel_path>')
def stream_music(rel_path):
    """Permet au lecteur audio intégré d'écouter le morceau directement sur téléphone et PC."""
    cfg = load_config()
    music_base = cfg.get("music_folder", "Musique")
    full_path = os.path.normpath(os.path.join(music_base, rel_path))

    if not full_path.startswith(os.path.normpath(music_base)) or not os.path.exists(full_path):
        return abort(404)

    return send_file(full_path, mimetype='audio/mpeg')

@app.route('/api/download-file/<path:rel_path>')
def download_file(rel_path):
    """Permet au smartphone ou à l'ordinateur de télécharger le fichier MP3 directement dans sa mémoire."""
    cfg = load_config()
    music_base = cfg.get("music_folder", "Musique")
    full_path = os.path.normpath(os.path.join(music_base, rel_path))

    if not full_path.startswith(os.path.normpath(music_base)) or not os.path.exists(full_path):
        return abort(404)

    filename = os.path.basename(full_path)
    # En-têtes explicites pour forcer le téléchargement sur Android Chrome, iOS Safari et PC
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

@app.route('/api/download-ready/<task_id>')
def download_ready(task_id):
    """
    Appelé depuis le navigateur du téléphone pour récupérer directement le MP3 HD 320k
    une fois le traitement serveur terminé (conversion + tags).
    Utilisé pour le bouton 'Enregistrer sur ce téléphone' affiché automatiquement.
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

@app.route('/api/singer/discography')
def singer_discography():
    """
    Mode Chanteur Complet : Recherche tous les morceaux d'un chanteur
    et scanne l'ordinateur/téléphone pour repérer les doublons.
    """
    artist = request.args.get('artist', '').strip()
    if not artist:
        return jsonify({"error": "Nom d'artiste manquant"}), 400
    limit = int(request.args.get('limit', 50))
    data = scanner.search_singer_discography(artist, limit=limit)
    return jsonify(data)

@app.route('/api/singer/verify-folder')
def singer_verify_folder():
    """
    Scanner vérificateur de chanteur :
    Analyse tous les fichiers du dossier du chanteur et vérifie
    qu'ils appartiennent bien à ce chanteur (détecte les intrus et mauvaises attributions).
    """
    artist = request.args.get('artist', '').strip()
    if not artist:
        return jsonify({"error": "Nom d'artiste manquant"}), 400
    report = scanner.scan_and_verify_singer_folder(artist)
    return jsonify(report)

@app.route('/api/singer/verify-track')
def singer_verify_track():
    """Vérifie si un titre donné appartient bien au chanteur cible."""
    title = request.args.get('title', '').strip()
    artist = request.args.get('artist', '').strip()
    target = request.args.get('target', '').strip()
    if not title or not target:
        return jsonify({"error": "Paramètres manquants"}), 400
    res = scanner.verify_track_artist(title, artist, target)
    return jsonify(res)

@app.route('/api/singer/create-files', methods=['POST'])
def singer_create_files():
    """Crée les fichiers dédiés du chanteur (dossier, playlist .m3u8, discographie.json, texte)."""
    data = request.json or {}
    artist = data.get('artist', '').strip()
    tracks = data.get('tracks', [])
    if not artist:
        return jsonify({"error": "Nom d'artiste manquant"}), 400
    res = scanner.create_artist_files_and_playlist(artist, tracks)
    return jsonify({"success": True, "files": res})

@app.route('/api/singer/download-all', methods=['POST'])
def singer_download_all():
    """Télécharge l'intégralité des morceaux du chanteur en évitant les doublons."""
    data = request.json or {}
    artist = data.get('artist', '').strip()
    tracks = data.get('tracks', [])
    skip_duplicates = data.get('skip_duplicates', True)

    if not artist or not tracks:
        return jsonify({"error": "Données incomplètes"}), 400

    task_id = download_singer_discography_async(
        artist_name=artist,
        tracks=tracks,
        skip_duplicates=skip_duplicates
    )
    return jsonify({"task_id": task_id, "status": "started"})

@app.route('/api/phone/register-music', methods=['POST'])
def phone_register_music():
    """
    Permet au téléphone d'envoyer la liste des titres qu'il possède
    pour que le scanner anti-doublon les ignore.
    """
    data = request.json or {}
    tracks = data.get('tracks', [])
    count = scanner.register_phone_music(tracks)
    return jsonify({"success": True, "registered_count": count})

@app.route('/api/scanner/summary')
def scanner_summary():
    """Renvoie le résumé des morceaux existants sur le PC et le téléphone."""
    existing = scanner.scan_all_existing_music()
    return jsonify({
        "total_existing": len(existing),
        "pc_count": len([x for x in existing if "PC" in x.get("source", "") or "App" in x.get("source", "")]),
        "phone_count": len([x for x in existing if "Téléphone" in x.get("source", "")])
    })

@app.route('/api/singer/download-zip/<path:artist_name>')
def download_artist_zip(artist_name):
    """
    Permet au smartphone ou à l'ordinateur de télécharger l'intégralité du dossier
    du chanteur (tous les MP3 HD 320k + playlist .m3u8) sous la forme d'un fichier .ZIP.
    """
    import zipfile
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

if __name__ == '__main__':
    ip = get_local_ip()
    sep = "=" * 65
    print(sep)
    print(" APPLICATION TELECHARGEUR MP3 POUR TELEPHONE ET ORDINATEUR")
    print(sep)
    print(f" PC    : http://localhost:{PORT}")
    print(f" Tel   : http://{ip}:{PORT}")
    print(sep)
    print(" Scannez le QR Code dans l'interface ou connectez votre telephone")
    print(" au meme reseau WiFi pour l'utiliser sur smartphone !")
    print(sep)

    # Ouvrir automatiquement le navigateur sur PC
    def open_browser():
        import time
        time.sleep(1.2)
        try:
            webbrowser.open(f"http://localhost:{PORT}")
        except Exception:
            pass

    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT, debug=False)
