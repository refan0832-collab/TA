import json
import time
from datetime import datetime
import threading
import paho.mqtt.client as mqtt

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "test/listrik/data"

current_data = {}
history = []
start_time = time.time()
last_esp_timestamp = 0  # Waktu terakhir data dari ESP diterima via MQTT

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ MQTT Connected")
        client.subscribe(MQTT_TOPIC)
    else:
        print("❌ MQTT Failed:", rc)

def on_message(client, userdata, msg):
    global current_data, history, last_esp_timestamp

    try:
        payload = msg.payload.decode()
        data = json.loads(payload)

        # Mapping dari ESP32
        mapped = {
            "voltage": data.get("tegangan"),
            "current": data.get("arus"),
            "power": data.get("daya"),
            "frequency": data.get("frekuensi"),
            "timestamp": datetime.now().isoformat()
        }

        current_data = mapped
        history.append(mapped)
        last_esp_timestamp = time.time()  # Catat waktu terakhir data masuk

        if len(history) > 500:
            history.pop(0)

        print("📥 Data MQTT:", mapped)
        print("🕐 last_esp_timestamp updated:", datetime.fromtimestamp(last_esp_timestamp).strftime("%H:%M:%S"))

    except Exception as e:
        print("❌ Error parsing:", e)

def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    thread = threading.Thread(target=client.loop_forever)
    thread.daemon = True
    thread.start()

def get_current_data():
    return current_data

def get_history(limit=100):
    return history[-limit:]

def get_status():
    return {
        "status": "online",
        "uptime": int(time.time() - start_time),
        "data_points": len(history)
    }

def get_esp_status():
    """Cek apakah ESP32 online berdasarkan waktu terakhir data diterima"""
    global last_esp_timestamp
    now = time.time()
    time_since_last = now - last_esp_timestamp

    print(f"[ESP Status] last_esp_timestamp: {last_esp_timestamp}")
    print(f"[ESP Status] now: {now}")
    print(f"[ESP Status] time_since_last: {time_since_last}")

    # Jika dalam 10 detik terakhir ada data = Online
    if last_esp_timestamp > 0 and time_since_last < 10:
        result = {
            "esp_online": True,
            "last_seen_seconds": int(time_since_last),
            "last_seen": datetime.fromtimestamp(last_esp_timestamp).strftime("%H:%M:%S")
        }
        print(f"[ESP Status] Result: {result}")
        return result
    else:
        result = {
            "esp_online": False,
            "last_seen_seconds": int(time_since_last) if last_esp_timestamp > 0 else None,
            "last_seen": None
        }
        print(f"[ESP Status] Result: {result}")
        return result