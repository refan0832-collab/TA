from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime, timedelta
import hashlib
import secrets
import time
import os

# =============================
# BLUEPRINT
# =============================
auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth"
)

# =============================
# CONFIG
# =============================
TOKEN_EXPIRY_HOURS = 8

SECRET_SALT = os.environ.get(
    "PM_SECRET",
    "esp32-powermonitor-secret-2025"
)

# =============================
# HASH PASSWORD
# =============================
def _hash_password(password):

    salted = f"{SECRET_SALT}:{password}"

    return hashlib.sha256(
        salted.encode()
    ).hexdigest()

# =============================
# DATABASE USER
# =============================
USERS_DB = {

    "admin": {

        "password_hash":
            _hash_password("admin123"),

        "role":
            "admin",

        "display_name":
            "Administrator"
    }
}

# =============================
# TOKEN STORE
# =============================
_active_tokens = {}

# =============================
# GENERATE TOKEN
# =============================
def _generate_token(username, role):

    token = secrets.token_urlsafe(32)

    _active_tokens[token] = {

        "username":
            username,

        "role":
            role,

        "created_at":
            datetime.utcnow().isoformat(),

        "expires_at":
            (
                datetime.utcnow()
                + timedelta(
                    hours=TOKEN_EXPIRY_HOURS
                )
            ).isoformat(),

        "exp_timestamp":
            time.time()
            + TOKEN_EXPIRY_HOURS * 3600
    }

    print(
        f"🔑 Token baru untuk '{username}'"
    )

    return token

# =============================
# VALIDATE TOKEN
# =============================
def _validate_token(token):

    if (
        not token or
        token not in _active_tokens
    ):
        return None

    payload = _active_tokens[token]

    if (
        time.time() >
        payload["exp_timestamp"]
    ):

        del _active_tokens[token]

        return None

    return payload

# =============================
# REQUIRE AUTH
# =============================
def require_auth(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        auth_header = request.headers.get(
            "Authorization",
            ""
        )

        if not auth_header.startswith(
            "Bearer "
        ):

            return jsonify({
                "error":
                    "Token tidak ditemukan"
            }), 401

        token = auth_header.split(
            " ",
            1
        )[1].strip()

        payload = _validate_token(token)

        if payload is None:

            return jsonify({
                "error":
                    "Token tidak valid"
            }), 401

        request.current_user = {

            "username":
                payload["username"],

            "role":
                payload["role"]
        }

        return f(*args, **kwargs)

    return decorated

# =============================
# LOGIN
# =============================
@auth_bp.route(
    "/login",
    methods=["POST"]
)
def login():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "error":
                "Body JSON diperlukan"
        }), 400

    username = str(
        data.get("username", "")
    ).strip().lower()

    password = str(
        data.get("password", "")
    ).strip()

    if (
        not username or
        not password
    ):

        return jsonify({
            "error":
                "Username dan password wajib diisi"
        }), 400

    user = USERS_DB.get(username)

    if not user:

        return jsonify({
            "error":
                "Username atau password salah"
        }), 401

    if (
        user["password_hash"] !=
        _hash_password(password)
    ):

        return jsonify({
            "error":
                "Username atau password salah"
        }), 401

    token = _generate_token(
        username,
        user["role"]
    )

    print(
        f"✅ Login berhasil: {username}"
    )

    return jsonify({

        "token":
            token,

        "username":
            username,

        "role":
            user["role"],

        "display_name":
            user["display_name"],

        "expires_in":
            TOKEN_EXPIRY_HOURS * 3600

    }), 200

# =============================
# LOGOUT
# =============================
@auth_bp.route(
    "/logout",
    methods=["POST"]
)
def logout():

    auth_header = request.headers.get(
        "Authorization",
        ""
    )

    if auth_header.startswith(
        "Bearer "
    ):

        token = auth_header.split(
            " ",
            1
        )[1].strip()

        if token in _active_tokens:

            del _active_tokens[token]

    return jsonify({
        "message":
            "Logout berhasil"
    })

# =============================
# VERIFY
# =============================
@auth_bp.route(
    "/verify",
    methods=["GET"]
)
def verify():

    auth_header = request.headers.get(
        "Authorization",
        ""
    )

    if not auth_header.startswith(
        "Bearer "
    ):

        return jsonify({
            "valid": False
        })

    token = auth_header.split(
        " ",
        1
    )[1].strip()

    payload = _validate_token(token)

    if payload:

        return jsonify({

            "valid":
                True,

            "username":
                payload["username"],

            "role":
                payload["role"]
        })

    return jsonify({
        "valid": False
    })