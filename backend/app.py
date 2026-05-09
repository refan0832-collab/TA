from flask import Flask, jsonify
from flask_cors import CORS
import mqtt_client

from login import auth_bp

app = Flask(__name__)
CORS(app)

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

if __name__ == "__main__":

    print(
        "🚀 Backend Running di http://localhost:5000"
    )

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )