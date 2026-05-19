import os
import sys

# =========================
# ROOT PROJECT
# =========================

ROOT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

BACKEND_DIR = os.path.join(
    ROOT_DIR,
    "backend"
)

FRONTEND_DIR = os.path.join(
    ROOT_DIR,
    "frontend"
)

# =========================
# PYTHON PATH
# =========================

sys.path.insert(0, BACKEND_DIR)

# =========================
# IMPORT FLASK APP
# =========================

from flask import render_template
from app import app

# =========================
# SET FRONTEND FOLDER
# =========================

app.template_folder = FRONTEND_DIR
app.static_folder = FRONTEND_DIR

# =========================
# FRONTEND ROUTES
# =========================

@app.route("/")
def login_page():

    return render_template(
        "login.html"
    )


@app.route("/dashboard")
def dashboard():

    return render_template(
        "index.html"
    )


@app.route("/history")
def history_page():

    return render_template(
        "history.html"
    )


@app.route("/settings")
def settings_page():

    return render_template(
        "settings.html"
    )

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    print(
        "\n🚀 PowerMonitor Running"
    )

    print(
        "http://localhost:5000"
    )

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )