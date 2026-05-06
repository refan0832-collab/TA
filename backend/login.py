"""
==================================
LOGIN BACKEND — login.py
PowerMonitor ESP32 Auth System
==================================

Endpoint:
  POST /api/auth/login    → { token, username, role }
  POST /api/auth/logout   → { message }
  GET  /api/auth/me       → { username, role }
  GET  /api/auth/verify   → { valid: true/false }

Daftarkan Blueprint di app.py:
    from login import auth_bp
    app.register_blueprint(auth_bp)
==================================
"""

import os
import time
import hashlib
import secrets
from functools import wraps
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

# =============================
# BLUEPRINT
# =============================
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# =============================
# CONFIG
# =============================
TOKEN_EXPIRY_HOURS = 8          # token berlaku 8 jam
SECRET_SALT = os.environ.get("PM_SECRET", "esp32-powermonitor-secret-2025")

# =============================
# DATABASE USER (in-memory)
# Ganti dengan database sungguhan di produksi!
# =============================
USERS_DB = {
    "admin": {
        "password_hash": _hash_password("admin123"),
        "role": "admin",
        "display_name": "Administrator"
    },
    "operator": {
        "password_hash": _hash_password("operator1"),
        "role": "operator",
        "display_name": "Operator"
    },
    "viewer": {
        "password_hash": _hash_password("viewer123"),
        "role": "viewer",
        "display_name": "Viewer"
    },
}

# =============================
# TOKEN STORE (in-memory)
# Ganti dengan Redis di produksi!
# =============================
_active_tokens: dict[str, dict] = {}


# =============================
# HELPER: HASH PASSWORD
# =============================
def _hash_password(password: str) -> str:
    """SHA-256 sederhana + salt. Gunakan bcrypt di produksi."""
    salted = f"{SECRET_SALT}:{password}"
    return hashlib.sha256(salted.encode()).hexdigest()


# =============================
# HELPER: BUAT TOKEN
# =============================
def _generate_token(username: str, role: str) -> str:
    """Buat token acak dan simpan ke store."""
    token = secrets.token_urlsafe(32)
    _active_tokens[token] = {
        "username": username,
        "role": role,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)).isoformat(),
        "exp_timestamp": time.time() + TOKEN_EXPIRY_HOURS * 3600
    }
    print(f"🔑 Token baru untuk '{username}' — expires {TOKEN_EXPIRY_HOURS}h")
    return token


# =============================
# HELPER: VALIDASI TOKEN
# =============================
def _validate_token(token: str) -> dict | None:
    """
    Kembalikan payload token jika valid dan belum kadaluarsa.
    Return None jika tidak valid atau sudah expired.
    """
    if not token or token not in _active_tokens:
        return None

    payload = _active_tokens[token]

    # Cek expiry
    if time.time() > payload["exp_timestamp"]:
        del _active_tokens[token]  # hapus token expired
        print(f"⏰ Token expired untuk '{payload['username']}'")
        return None

    return payload


# =============================
# DECORATOR: REQUIRE LOGIN
# =============================
def require_auth(f):
    """
    Decorator untuk endpoint yang butuh login.

    Cara pakai:
        @app.route("/api/protected")
        @require_auth
        def protected_route():
            ...

    Token dikirim lewat header:
        Authorization: Bearer <token>
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token tidak ditemukan"}), 401

        token = auth_header.split(" ", 1)[1].strip()
        payload = _validate_token(token)

        if payload is None:
            return jsonify({"error": "Token tidak valid atau sudah kadaluarsa"}), 401

        # Inject user info ke request context
        request.current_user = {
            "username": payload["username"],
            "role": payload["role"]
        }

        return f(*args, **kwargs)

    return decorated


# =============================
# ENDPOINT: LOGIN
# =============================
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /api/auth/login
    Body: { "username": "...", "password": "..." }
    Response: { "token": "...", "username": "...", "role": "...", "expires_in": 28800 }
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Body JSON diperlukan"}), 400

    username = str(data.get("username", "")).strip().lower()
    password = str(data.get("password", "")).strip()

    # Validasi input
    if not username or not password:
        return jsonify({"error": "Username dan password wajib diisi"}), 400

    # Cek user
    user = USERS_DB.get(username)
    if not user:
        print(f"🚫 Login gagal: user '{username}' tidak ditemukan")
        return jsonify({"error": "Username atau password salah"}), 401

    # Cek password
    if user["password_hash"] != _hash_password(password):
        print(f"🚫 Login gagal: password salah untuk '{username}'")
        return jsonify({"error": "Username atau password salah"}), 401

    # Buat token
    token = _generate_token(username, user["role"])

    print(f"✅ Login berhasil: '{username}' ({user['role']})")

    return jsonify({
        "token":      token,
        "username":   username,
        "role":       user["role"],
        "display_name": user["display_name"],
        "expires_in": TOKEN_EXPIRY_HOURS * 3600   # dalam detik
    }), 200


# =============================
# ENDPOINT: LOGOUT
# =============================
@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    POST /api/auth/logout
    Header: Authorization: Bearer <token>
    Menghapus token dari store.
    """
    auth_header = request.headers.get("Authorization", "")

    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        if token in _active_tokens:
            username = _active_tokens[token]["username"]
            del _active_tokens[token]
            print(f"🚪 Logout: '{username}'")

    return jsonify({"message": "Logout berhasil"}), 200


# =============================
# ENDPOINT: GET CURRENT USER
# =============================
@auth_bp.route("/me", methods=["GET"])
@require_auth
def me():
    """
    GET /api/auth/me
    Header: Authorization: Bearer <token>
    Response: { "username": "...", "role": "..." }
    """
    return jsonify(request.current_user), 200


# =============================
# ENDPOINT: VERIFY TOKEN
# =============================
@auth_bp.route("/verify", methods=["GET"])
def verify():
    """
    GET /api/auth/verify
    Header: Authorization: Bearer <token>
    Response: { "valid": true/false }
    Dipakai frontend untuk cek sesi masih aktif.
    """
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return jsonify({"valid": False}), 200

    token = auth_header.split(" ", 1)[1].strip()
    payload = _validate_token(token)

    if payload:
        return jsonify({
            "valid": True,
            "username": payload["username"],
            "role": payload["role"]
        }), 200

    return jsonify({"valid": False}), 200


# =============================
# UTIL: TAMBAH USER BARU
# =============================
def add_user(username: str, password: str, role: str = "viewer", display_name: str = "") -> bool:
    """
    Tambah user baru ke USERS_DB.
    Panggil dari app.py atau shell untuk manajemen user.

    Contoh:
        from login import add_user
        add_user("budi", "budi123", role="operator")
    """
    username = username.strip().lower()

    if username in USERS_DB:
        print(f"⚠ User '{username}' sudah ada")
        return False

    USERS_DB[username] = {
        "password_hash": _hash_password(password),
        "role": role,
        "display_name": display_name or username.capitalize()
    }

    print(f"✅ User '{username}' ({role}) berhasil ditambahkan")
    return True


# =============================
# UTIL: HAPUS TOKEN EXPIRED (cleanup)
# =============================
def cleanup_expired_tokens():
    """Panggil secara berkala untuk bersihkan token expired dari memory."""
    now = time.time()
    expired = [t for t, p in _active_tokens.items() if now > p["exp_timestamp"]]
    for t in expired:
        del _active_tokens[t]
    if expired:
        print(f"🧹 {len(expired)} token expired dihapus")