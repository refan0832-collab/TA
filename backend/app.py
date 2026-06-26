from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    send_file
)

from flask_cors import CORS

import mqtt_client
import kwh_storage
import sensor_storage

from login import auth_bp, require_auth

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
# INIT SQLite
# =========================
sensor_storage.init_db()

# =========================
# RELAY STATE
# =========================

relay_state = {
    19: False,
    21: False
}

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

@app.route("/controller")
def controller_page():

    return render_template(
        "controller.html"
    )

# =========================
# API RELAY CONTROL
# =========================

@app.route("/api/relay/control", methods=["POST"])
def relay_control():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Body JSON diperlukan"}), 400

    pin = data.get("pin")
    state = data.get("state")

    if pin not in [19, 21]:
        return jsonify({"error": "Pin tidak valid. Gunakan pin 19 atau 21"}), 400

    if not isinstance(state, bool):
        return jsonify({"error": "State harus boolean (true/false)"}), 400

    payload = {
        "pin": pin,
        "state": state
    }

    success = mqtt_client.publish_relay(payload)

    if not success:
        return jsonify({"error": "Gagal mengirim perintah ke MQTT"}), 500

    relay_state[pin] = state

    print(f"🔁 Relay PIN {pin} → {'ON' if state else 'OFF'}")

    return jsonify({
        "pin":    pin,
        "state":  state,
        "status": "ok"
    }), 200

# =========================
# API RELAY STATUS
# =========================

@app.route("/api/relay/status")
def relay_status():

    return jsonify({
        19: relay_state[19],
        21: relay_state[21]
    })

# =========================
# API CURRENT
# [DIUPDATE] tambah field energy, overvoltage, undervoltage
# =========================

@app.route("/api/current")
def current():

    data = mqtt_client.get_current_data()

    return jsonify({

        "tegangan":
            float(
                data.get("tegangan", 0) or 0
            ),

        "arus":
            float(
                data.get("arus", 0) or 0
            ),

        "daya":
            float(
                data.get("daya", 0) or 0
            ),

        "frekuensi":
            float(
                data.get("frekuensi", 0) or 0
            ),

        "pf":
            float(
                data.get("pf", 0) or 0
            ),

        # [BARU] kWh akumulatif dari PZEM
        "energy":
            float(
                data.get("energy", 0) or 0
            ),

        # [BARU] status relay proteksi
        "overvoltage":
            bool(
                data.get("overvoltage", False)
            ),

        "undervoltage":
            bool(
                data.get("undervoltage", False)
            )
    })

# =========================
# [BARU] API PROTECTION STATUS
# Endpoint khusus untuk status relay proteksi PIN 22 & 23
# =========================

@app.route("/api/protection")
def protection_status():

    data = mqtt_client.get_current_data()

    return jsonify({

        "overvoltage": {
            "active":    bool(data.get("overvoltage", False)),
            "pin":       22,
            "threshold": 240.0,
            "voltage":   float(data.get("tegangan", 0) or 0)
        },

        "undervoltage": {
            "active":    bool(data.get("undervoltage", False)),
            "pin":       23,
            "threshold": 200.0,
            "voltage":   float(data.get("tegangan", 0) or 0)
        }
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
# API kWh RESET
# =========================

@app.route("/api/kwh/reset", methods=["POST"])
def kwh_reset():
    kwh_storage.reset_kwh()
    print("🗑️  Data kWh direset")
    return jsonify({"status": "ok", "message": "Data kWh berhasil direset"})

# =========================
# API kWh HISTORY
# =========================

@app.route("/api/kwh/history")
def kwh_history():
    return jsonify(kwh_storage.get_kwh_history())

# =========================
# API kWh TODAY
# =========================

@app.route("/api/kwh/today")
def kwh_today():
    return jsonify(kwh_storage.get_kwh_today())

# =========================
# =========================
# API SENSOR HISTORY — data hari ini dari SQLite
# =========================

@app.route("/api/sensor/today")
def sensor_today():
    return jsonify(sensor_storage.get_today())

# =========================
# API SENSOR BY DATE
# =========================

@app.route("/api/sensor/date/<date_str>")
def sensor_by_date(date_str):
    return jsonify(sensor_storage.get_by_date(date_str))

# =========================
# API DAFTAR TANGGAL TERSEDIA
# =========================

@app.route("/api/sensor/dates")
def sensor_dates():
    return jsonify(sensor_storage.get_available_dates())

# =========================
# API DAFTAR FILE EXCEL
# =========================

@app.route("/api/sensor/exports")
def sensor_exports():
    return jsonify(sensor_storage.get_export_files())

# =========================
# API DOWNLOAD FILE EXCEL
# =========================

@app.route("/api/sensor/download/<date_str>")
def sensor_download(date_str):

    import os

    # Coba ambil file yang sudah ada
    export_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "exports",
        f"sensor_{date_str}.xlsx"
    )

    # Kalau belum ada, generate dulu
    if not os.path.exists(export_path):
        result = sensor_storage.export_daily_excel(date_str)
        if result is None:
            return jsonify({"error": "Tidak ada data untuk tanggal tersebut"}), 404
        export_path = result

    return send_file(
        export_path,
        as_attachment=True,
        download_name=f"sensor_{date_str}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =========================
# API TRIGGER EXPORT + CLEANUP MANUAL
# =========================

@app.route("/api/sensor/export-today", methods=["POST"])
def sensor_export_today():
    today = __import__('datetime').datetime.now().strftime("%Y-%m-%d")
    result = sensor_storage.export_daily_excel(today)
    sensor_storage.cleanup_old_data()
    if result:
        return jsonify({"status": "ok", "file": f"sensor_{today}.xlsx"})
    return jsonify({"error": "Tidak ada data hari ini"}), 404

# =========================
# =========================
# API SENSOR RESET BY DATE
# =========================

@app.route("/api/sensor/reset/<date_str>", methods=["POST"])
def sensor_reset_by_date(date_str):
    deleted = sensor_storage.reset_by_date(date_str)
    return jsonify({
        "status":  "ok",
        "date":    date_str,
        "deleted": deleted,
        "message": f"{deleted} record tanggal {date_str} dihapus"
    })

# =========================
# DEBUG
# =========================
# =========================

@app.route("/api/debug")
def debug():

    data = mqtt_client.get_current_data()

    return jsonify({

        "current_data": {

            "tegangan":    float(data.get("tegangan",    0) or 0),
            "arus":        float(data.get("arus",        0) or 0),
            "daya":        float(data.get("daya",        0) or 0),
            "frekuensi":   float(data.get("frekuensi",   0) or 0),
            "pf":          float(data.get("pf",          0) or 0),
            "energy":      float(data.get("energy",      0) or 0),
            "overvoltage": bool(data.get("overvoltage",  False)),
            "undervoltage":bool(data.get("undervoltage", False))
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

    # =========================
    # AUTO EXPORT + CLEANUP HARIAN
    # =========================
    import threading
    import time as _time
    from datetime import datetime as _dt

    def daily_task():
        last_date = _dt.now().strftime("%Y-%m-%d")
        while True:
            _time.sleep(60)  # cek setiap 1 menit
            today = _dt.now().strftime("%Y-%m-%d")
            if today != last_date:
                print(f"📅 Ganti hari → export {last_date} & cleanup")
                sensor_storage.export_daily_excel(last_date)
                sensor_storage.cleanup_old_data()
                last_date = today

    t = threading.Thread(target=daily_task, daemon=True)
    t.start()

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