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

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ MQTT Connected")
        client.subscribe(MQTT_TOPIC)
    else:
        print("❌ MQTT Failed:", rc)

def on_message(client, userdata, msg):
    global current_data, history

    try:
        payload = msg.payload.decode()
        data = json.loads(payload)

        # Mapping dari ESP32
        mapped = {
            "voltage": data.get("tegangan"),
            "current": data.get("arus"),
            "power": data.get("daya"),
            "timestamp": datetime.now().isoformat()
        }

        current_data = mapped
        history.append(mapped)

        if len(history) > 500:
            history.pop(0)

        print("📥 Data MQTT:", mapped)

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