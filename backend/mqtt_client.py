import json
import time
import threading

from datetime import datetime

import paho.mqtt.client as mqtt
import kwh_storage
import sensor_storage

# =========================
# MQTT CONFIG
# =========================

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

MQTT_TOPIC = "esp32/power_monitor"
MQTT_RELAY_TOPIC = "esp32/control"

# =========================
# STORAGE
# =========================

current_data = {

    "tegangan":     0,
    "arus":         0,
    "daya":         0,
    "frekuensi":    0,
    "pf":           0,
    "energy":       0,       # [BARU] kWh akumulatif dari PZEM
    "overvoltage":  False,   # [BARU] status relay proteksi PIN 22
    "undervoltage": False,   # [BARU] status relay proteksi PIN 23
    "timestamp":    None
}

history = []

start_time = time.time()

# WAKTU TERAKHIR DATA ESP
last_esp_timestamp = 0

# MQTT CLIENT GLOBAL (untuk publish)
_mqtt_client = None

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

            "pf":
                float(
                    data.get(
                        "pf",
                        0
                    )
                ),

            # [BARU] kWh akumulatif dari PZEM
            "energy":
                float(
                    data.get(
                        "energy",
                        0
                    )
                ),

            # [BARU] status relay proteksi
            "overvoltage":
                bool(
                    data.get(
                        "overvoltage",
                        False
                    )
                ),

            "undervoltage":
                bool(
                    data.get(
                        "undervoltage",
                        False
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

        # [FIX] interval disesuaikan dengan interval kirim ESP (2 detik)
        kwh_storage.update_kwh(mapped["daya"], interval_seconds=2)

        # [BARU] Simpan ke SQLite
        sensor_storage.save_sensor(mapped)

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

        if mapped["overvoltage"]:
            print("⚠️  OVERVOLTAGE ACTIVE (Pin 22)")

        if mapped["undervoltage"]:
            print("⚠️  UNDERVOLTAGE ACTIVE (Pin 23)")

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

    global _mqtt_client

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

    _mqtt_client = client

    thread = threading.Thread(
        target=client.loop_forever
    )

    thread.daemon = True

    thread.start()

# =========================
# PUBLISH RELAY
# =========================

def publish_relay(payload):

    global _mqtt_client

    if _mqtt_client is None:
        print("❌ MQTT client belum siap")
        return False

    try:

        message = json.dumps(payload)

        result = _mqtt_client.publish(
            MQTT_RELAY_TOPIC,
            message
        )

        if result.rc == 0:
            print(
                f"📤 RELAY → PIN {payload['pin']} "
                f"{'ON' if payload['state'] else 'OFF'}"
            )
            return True

        print("❌ Publish gagal, rc:", result.rc)
        return False

    except Exception as e:
        print("❌ Publish error:", e)
        return False

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