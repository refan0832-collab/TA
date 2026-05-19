from flask import Flask, jsonify, request
from flask_cors import CORS
import mqtt_client

from login import auth_bp

app = Flask(__name__)

# CORS configuration - allow all origins with proper headers
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# REGISTER LOGIN API
app.register_blueprint(auth_bp)

# START MQTT
mqtt_client.start_mqtt()

@app.route("/")
def home():
    return {
        "message": "Backend Running"
    }

@app.route("/api/current")
def current():
    return jsonify(
        mqtt_client.get_current_data()
    )

@app.route("/api/history")
def history():
    return jsonify(
        mqtt_client.get_history()
    )

@app.route("/api/status")
def status():
    return jsonify(
        mqtt_client.get_status()
    )

@app.route("/api/esp-status")
def esp_status():
    """Endpoint untuk cek status ESP32 (online/offline berdasarkan MQTT)"""
    return jsonify(
        mqtt_client.get_esp_status()
    )

@app.route("/api/debug")
def debug():
    return {
        "current_data":
            mqtt_client.get_current_data(),

        "history_len":
            len(
                mqtt_client.get_history()
            ),
    }

# Handle OPTIONS requests explicitly for CORS preflight
@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    response = jsonify({"status": "ok"})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

if __name__ == "__main__":

    print(
        "🚀 Backend Running di http://localhost:5000"
    )

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )