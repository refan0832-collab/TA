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

# =========================
# PYTHON PATH
# =========================

sys.path.insert(
    0,
    BACKEND_DIR
)

# =========================
# IMPORT APP
# =========================

from app import app

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    print()
    print("================================")
    print("🚀 PowerMonitor Running")
    print("================================")

    print(
        "🌐 URL : http://localhost:5000"
    )

    print(
        "📡 MQTT Monitoring Active"
    )

    print(
        "⚡ ESP32 Power Monitor Ready"
    )

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=False,
        use_reloader=False
    )