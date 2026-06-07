from flask import (
    Flask,
    jsonify,
    render_template
)

from flask_cors import CORS

import mqtt_client

from login import auth_bp

# =========================
# APP
# =========================

app = Flask(

    __name__,

    template_folder="../frontend",

    static_folder="../frontend"
)

# =========================
# SECRET KEY
# =========================

app.config["SECRET_KEY"] = \
    "powermonitor-secret"

# =========================
# CORS
# =========================

CORS(app)

# =========================
# REGISTER AUTH
# =========================

app.register_blueprint(auth_bp)

# =========================
# START MQTT
# =========================

mqtt_client.start_mqtt()

# =========================
# FRONTEND ROUTES
# =========================

@app.route("/")
def login_page():

    return render_template(
        "login.html"
    )

# =========================

@app.route("/dashboard")
def dashboard():

    return render_template(
        "index.html"
    )

# =========================

@app.route("/history-page")
def history_page():

    return render_template(
        "history.html"
    )

# =========================

@app.route("/settings")
def settings_page():

    return render_template(
        "settings.html"
    )

# =========================
# API CURRENT
# =========================

@app.route("/api/current")
def current():

    data = mqtt_client.get_current_data()

    return jsonify({

        "tegangan":

            float(
                data.get(
                    "tegangan",
                    0
                ) or 0
            ),

        "arus":

            float(
                data.get(
                    "arus",
                    0
                ) or 0
            ),

        "daya":

            float(
                data.get(
                    "daya",
                    0
                ) or 0
            ),

        "frekuensi":

            float(
                data.get(
                    "frekuensi",
                    0
                ) or 0
            ),

        "pf":

            float(
                data.get(
                    "pf",
                    0
                ) or 0
            )
    })

# =========================
# API HISTORY
# =========================

@app.route("/api/history")
def history():

    return jsonify(
        mqtt_client.get_history()
    )

# =========================
# API STATUS
# =========================

@app.route("/api/status")
def status():

    return jsonify(
        mqtt_client.get_status()
    )

# =========================
# API ESP STATUS
# =========================

@app.route("/api/esp-status")
def esp_status():

    return jsonify(
        mqtt_client.get_esp_status()
    )

# =========================
# DEBUG
# =========================

@app.route("/api/debug")
def debug():

    data = mqtt_client.get_current_data()

    return jsonify({

        "current_data": {

            "tegangan":

                float(
                    data.get(
                        "tegangan",
                        0
                    ) or 0
                ),

            "arus":

                float(
                    data.get(
                        "arus",
                        0
                    ) or 0
                ),

            "daya":

                float(
                    data.get(
                        "daya",
                        0
                    ) or 0
                ),

            "frekuensi":

                float(
                    data.get(
                        "frekuensi",
                        0
                    ) or 0
                ),

            "pf":

                float(
                    data.get(
                        "pf",
                        0
                    ) or 0
                )
        },

        "history_len":

            len(
                mqtt_client.get_history()
            )
    })

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    print()
    print("================================")
    print("🚀 Backend Running")
    print("================================")

    print(
        "🌐 http://localhost:5000"
    )

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True
    )