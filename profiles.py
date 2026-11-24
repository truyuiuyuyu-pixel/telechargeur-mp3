# -*- coding: utf-8 -*-
"""
profiles.py — Gestion des comptes, profils style Disney+ et reprise de lecture
Stockage local léger en JSON, thread-safe, sans dépendance externe.
"""

import os
import re
import json
import time
import hmac
import hashlib
import secrets
import threading

EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'profiles_data.json')
_LOCK = threading.Lock()

AVATAR_PRESETS = [
    {"id": "star", "icon": "fa-star", "gradient": "linear-gradient(135deg, #0063e5, #00d2ff)"},
    {"id": "rocket", "icon": "fa-rocket", "gradient": "linear-gradient(135deg, #6366f1, #a855f7)"},
    {"id": "crown", "icon": "fa-crown", "gradient": "linear-gradient(135deg, #f59e0b, #ef4444)"},
    {"id": "bolt", "icon": "fa-bolt", "gradient": "linear-gradient(135deg, #06b6d4, #3b82f6)"},
    {"id": "wand", "icon": "fa-wand-magic-sparkles", "gradient": "linear-gradient(135deg, #ec4899, #8b5cf6)"},
    {"id": "dragon", "icon": "fa-dragon", "gradient": "linear-gradient(135deg, #10b981, #059669)"},
    {"id": "mask", "icon": "fa-mask", "gradient": "linear-gradient(135deg, #ef4444, #b91c1c)"},
    {"id": "meteor", "icon": "fa-meteor", "gradient": "linear-gradient(135deg, #8b5cf6, #0284c7)"},
]


def _load_data():
    if not os.path.exists(DATA_FILE):
        data = {
            "secret": secrets.token_hex(32),
            "accounts": {}
        }
        _save_data(data)
        return data
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if "secret" not in data:
            data["secret"] = secrets.token_hex(32)
        if "accounts" not in data:
            data["accounts"] = {}
        return data
    except Exception:
        return {"secret": secrets.token_hex(32), "accounts": {}}


def _save_data(data):
    tmp = DATA_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


def _hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100_000)
    return f"{salt}${dk.hex()}"


def _verify_password(password, stored):
    try:
        salt, hex_dk = stored.split('$', 1)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100_000)
        return hmac.compare_digest(dk.hex(), hex_dk)
    except Exception:
        return False


def _sign_token(username, secret):
    ts = str(int(time.time()))
    msg = f"{username}|{ts}".encode('utf-8')
    sig = hmac.new(secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()
    return f"{username}|{ts}|{sig}"


def verify_token(token):
    if not token or '|' not in token:
        return None
    try:
        parts = token.split('|')
        if len(parts) != 3:
            return None
        username, ts, sig = parts
        with _LOCK:
            data = _load_data()
            secret = data["secret"]
            if username not in data["accounts"]:
                return None
        msg = f"{username}|{ts}".encode('utf-8')
        expected = hmac.new(secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()
        if hmac.compare_digest(sig, expected):
            return username
        return None
    except Exception:
        return None


def _normalize_email(email):
    return (email or '').strip().lower()


def register_account(email, password, name=None):
    email_clean = _normalize_email(email)
    if not email_clean or not EMAIL_RE.match(email_clean):
        return False, "Veuillez saisir une adresse e-mail valide.", None
    if not password or len(password) < 6:
        return False, "Le mot de passe doit contenir au moins 6 caractères.", None

    display_name = (name or '').strip() or email_clean.split('@')[0]
    display_name = display_name[:20]

    with _LOCK:
        data = _load_data()
        if email_clean in data["accounts"]:
            return False, "Un compte existe déjà avec cette adresse e-mail.", None

        default_profile_id = secrets.token_hex(6)
        data["accounts"][email_clean] = {
            "email": email_clean,
            "username": display_name,
            "password_hash": _hash_password(password),
            "created_at": int(time.time()),
            "profiles": [
                {
                    "id": default_profile_id,
                    "name": display_name,
                    "avatar": "star",
                    "progress": []
                }
            ]
        }
        _save_data(data)
        token = _sign_token(email_clean, data["secret"])
        return True, "Compte créé avec succès.", {
            "token": token,
            "email": email_clean,
            "username": display_name,
            "profiles": _sanitize_profiles(data["accounts"][email_clean]["profiles"])
        }


def login_account(email, password):
    email_clean = _normalize_email(email)
    if not email_clean or not EMAIL_RE.match(email_clean):
        return False, "Veuillez saisir une adresse e-mail valide.", None
    if not password:
        return False, "Veuillez saisir votre mot de passe.", None

    with _LOCK:
        data = _load_data()
        acc = data["accounts"].get(email_clean)
        if not acc or not _verify_password(password, acc.get("password_hash", "")):
            return False, "Adresse e-mail ou mot de passe incorrect.", None

        token = _sign_token(email_clean, data["secret"])
        return True, "Connexion réussie.", {
            "token": token,
            "email": acc.get("email", email_clean),
            "username": acc.get("username", email_clean),
            "profiles": _sanitize_profiles(acc.get("profiles", []))
        }


def _sanitize_profiles(profiles):
    preset_map = {p["id"]: p for p in AVATAR_PRESETS}
    out = []
    for p in profiles:
        av_id = p.get("avatar", "star")
        av = preset_map.get(av_id, AVATAR_PRESETS[0])
        out.append({
            "id": p["id"],
            "name": p["name"],
            "avatar": av_id,
            "icon": av["icon"],
            "gradient": av["gradient"],
            "progress_count": len(p.get("progress", []))
        })
    return out


def get_account_info(username):
    uname = _normalize_email(username)
    with _LOCK:
        data = _load_data()
        acc = data["accounts"].get(uname)
        if not acc:
            return None
        return {
            "email": acc.get("email", uname),
            "username": acc.get("username", uname),
            "profiles": _sanitize_profiles(acc.get("profiles", []))
        }


def add_profile(username, name, avatar="star"):
    uname = _normalize_email(username)
    pname = (name or '').strip()
    if len(pname) < 1 or len(pname) > 20:
        return False, "Le nom du profil doit contenir entre 1 et 20 caractères.", None

    valid_avatars = {p["id"] for p in AVATAR_PRESETS}
    if avatar not in valid_avatars:
        avatar = "star"

    with _LOCK:
        data = _load_data()
        acc = data["accounts"].get(uname)
        if not acc:
            return False, "Compte introuvable.", None
        if len(acc["profiles"]) >= 8:
            return False, "Maximum 8 profils par compte.", None

        new_prof = {
            "id": secrets.token_hex(6),
            "name": pname,
            "avatar": avatar,
            "progress": []
        }
        acc["profiles"].append(new_prof)
        _save_data(data)
        return True, "Profil ajouté.", _sanitize_profiles(acc["profiles"])


def update_profile(username, profile_id, name=None, avatar=None):
    uname = _normalize_email(username)
    with _LOCK:
        data = _load_data()
        acc = data["accounts"].get(uname)
        if not acc:
            return False, "Compte introuvable.", None

        target = next((p for p in acc["profiles"] if p["id"] == profile_id), None)
        if not target:
            return False, "Profil introuvable.", None

        if name is not None:
            pname = name.strip()
            if len(pname) < 1 or len(pname) > 20:
                return False, "Nom invalide (1 à 20 caractères).", None
            target["name"] = pname

        if avatar is not None:
            valid_avatars = {p["id"] for p in AVATAR_PRESETS}
            if avatar in valid_avatars:
                target["avatar"] = avatar

        _save_data(data)
        return True, "Profil mis à jour.", _sanitize_profiles(acc["profiles"])


def delete_profile(username, profile_id):
    uname = _normalize_email(username)
    with _LOCK:
        data = _load_data()
        acc = data["accounts"].get(uname)
        if not acc:
            return False, "Compte introuvable.", None
        if len(acc["profiles"]) <= 1:
            return False, "Impossible de supprimer le dernier profil.", None

        acc["profiles"] = [p for p in acc["profiles"] if p["id"] != profile_id]
        _save_data(data)
        return True, "Profil supprimé.", _sanitize_profiles(acc["profiles"])


def get_profile_progress(username, profile_id):
    uname = _normalize_email(username)
    with _LOCK:
        data = _load_data()
        acc = data["accounts"].get(uname)
        if not acc:
            return []
        target = next((p for p in acc["profiles"] if p["id"] == profile_id), None)
        if not target:
            return []
        return list(target.get("progress", []))


def save_profile_progress(username, profile_id, item):
    uname = _normalize_email(username)
    if not item or not item.get("id"):
        return False, []

    with _LOCK:
        data = _load_data()
        acc = data["accounts"].get(uname)
        if not acc:
            return False, []
        target = next((p for p in acc["profiles"] if p["id"] == profile_id), None)
        if not target:
            return False, []

        prog_list = target.get("progress", [])
        item_id = str(item.get("id"))
        prog_list = [x for x in prog_list if str(x.get("id")) != item_id]

        entry = {
            "id": item_id,
            "title": (item.get("title") or "")[:120],
            "thumbnail": item.get("thumbnail") or "",
            "year": str(item.get("year") or ""),
            "is_series": bool(item.get("is_series")),
            "type_label": item.get("type_label") or ("Série" if item.get("is_series") else "Film Complet"),
            "embed_url": item.get("embed_url") or "",
            "season": int(item.get("season") or 1),
            "episode": int(item.get("episode") or 1),
            "server_idx": int(item.get("server_idx") or 1),
            "lang": item.get("lang") or "vf",
            "time_note": (item.get("time_note") or "")[:20],
            "updated_at": int(time.time())
        }
        prog_list.insert(0, entry)
        target["progress"] = prog_list[:30]
        _save_data(data)
        return True, target["progress"]


def remove_profile_progress(username, profile_id, item_id):
    uname = _normalize_email(username)
    with _LOCK:
        data = _load_data()
        acc = data["accounts"].get(uname)
        if not acc:
            return False, []
        target = next((p for p in acc["profiles"] if p["id"] == profile_id), None)
        if not target:
            return False, []

        target["progress"] = [x for x in target.get("progress", []) if str(x.get("id")) != str(item_id)]
        _save_data(data)
        return True, target["progress"]
