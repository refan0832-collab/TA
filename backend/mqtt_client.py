import json
import time
import threading

from datetime import datetime

import paho.mqtt.client as mqtt

# =========================
# MQTT CONFIG
# =========================

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

MQTT_TOPIC = "esp32/power_monitor"

# =========================
# STORAGE
# =========================

current_data = {

    "tegangan": 0,
    "arus": 0,
    "daya": 0,
    "frekuensi": 0,
    "pf": 0,

    "timestamp": None
}

history = []

start_time = time.time()

# WAKTU TERAKHIR DATA ESP
last_esp_timestamp = 0

# =========================
# MQTT CONNECT
# =========================

def on_connect(
    client,
    userdata,
    flags,
    rc
):

    if rc == 0:

        print("✅ MQTT Connected")

        client.subscribe(
            MQTT_TOPIC
        )

        print(
            f"📡 Subscribe: {MQTT_TOPIC}"
        )

    else:

        print(
            "❌ MQTT Failed:",
            rc
        )

# =========================
# MQTT MESSAGE
# =========================

def on_message(
    client,
    userdata,
    msg
):

    global current_data
    global history
    global last_esp_timestamp

    try:

        payload = \
            msg.payload.decode()

        data = json.loads(payload)

        # =========================
        # MAPPING DATA
        # =========================

        mapped = {

            "tegangan":
                float(
                    data.get(
                        "tegangan",
                        0
                    )
                ),

            "arus":
                float(
                    data.get(
                        "arus",
                        0
                    )
                ),

            "daya":
                float(
                    data.get(
                        "daya",
                        0
                    )
                ),

            "frekuensi":
                float(
                    data.get(
                        "frekuensi",
                        0
                    )
                ),

            # POWER FACTOR
            "pf":
                float(
                    data.get(
                        "pf",
                        0
                    )
                ),

            "timestamp":
                datetime.now()
                .isoformat()
        }

        # =========================
        # UPDATE STORAGE
        # =========================

        current_data = mapped

        history.append(mapped)

        last_esp_timestamp = \
            time.time()

        # LIMIT HISTORY
        if len(history) > 500:

            history.pop(0)

        # =========================
        # SERIAL LOG
        # =========================

        print()
        print("================================")
        print("📥 DATA MQTT")
        print(mapped)

        print(
            "🕐 LAST UPDATE:",
            datetime
            .fromtimestamp(
                last_esp_timestamp
            )
            .strftime("%H:%M:%S")
        )

    except Exception as e:

        print()
        print("================================")
        print("❌ MQTT PARSE ERROR")
        print(e)

# =========================
# START MQTT
# =========================

def start_mqtt():

    client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message

    print()
    print("================================")
    print("🚀 START MQTT")
    print("BROKER :", MQTT_BROKER)
    print("TOPIC  :", MQTT_TOPIC)

    client.connect(
        MQTT_BROKER,
        MQTT_PORT,
        60
    )

    thread = threading.Thread(
        target=client.loop_forever
    )

    thread.daemon = True

    thread.start()

# =========================
# GET CURRENT DATA
# =========================

def get_current_data():

    return current_data

# =========================
# GET HISTORY
# =========================

def get_history(limit=100):

    return history[-limit:]

# =========================
# GET STATUS
# =========================

def get_status():

    return {

        "status": "online",

        "uptime":
            int(
                time.time() -
                start_time
            ),

        "data_points":
            len(history)
    }

# =========================
# GET ESP STATUS
# =========================

def get_esp_status():

    global last_esp_timestamp

    now = time.time()

    time_since_last = \
        now - last_esp_timestamp

    # ONLINE < 10 DETIK
    esp_online = (
        last_esp_timestamp > 0 and
        time_since_last < 10
    )

    return {

        "esp_online":
            esp_online,

        "last_seen_seconds":

            int(time_since_last)

            if last_esp_timestamp > 0
            else None,

        "last_seen":

            datetime
            .fromtimestamp(
                last_esp_timestamp
            )
            .strftime("%H:%M:%S")

            if last_esp_timestamp > 0
            else None
    }
