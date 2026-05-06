#include <WiFi.h>
#include <PubSubClient.h>

// =======================
// WiFi Config
// =======================
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// =======================
// MQTT Config
// =======================
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;
const char* topic = "test/listrik/data";

WiFiClient espClient;
PubSubClient client(espClient);

// =======================
// TIMER
// =======================
unsigned long lastSend = 0;
const long interval = 2000; // kirim tiap 2 detik

// =======================
// WIFI CONNECT (NON BLOCKING)
// =======================
void connectWiFi() {
  static unsigned long lastAttempt = 0;

  if (WiFi.status() == WL_CONNECTED) return;

  if (millis() - lastAttempt > 5000) {
    lastAttempt = millis();

    Serial.println("🔄 Connecting WiFi...");
    WiFi.begin(ssid, password);
  }
}

// =======================
// MQTT CONNECT (NON BLOCKING)
// =======================
void connectMQTT() {
  static unsigned long lastAttempt = 0;

  if (client.connected()) return;

  if (millis() - lastAttempt > 5000) {
    lastAttempt = millis();

    String clientId = "ESP32-" + String(random(1000, 9999));

    Serial.print("🔄 Connecting MQTT... ");

    if (client.connect(clientId.c_str())) {
      Serial.println("✅ Connected");
    } else {
      Serial.print("❌ Failed, state=");
      Serial.println(client.state());
    }
  }
}

// =======================
// GENERATE DATA JSON
// =======================
String generateJSON() {
  float tegangan = random(210, 231);
  float arus = random(1, 6);
  float daya = tegangan * arus;

  String payload = "{";
  payload += "\"tegangan\":" + String(tegangan) + ",";
  payload += "\"arus\":" + String(arus) + ",";
  payload += "\"daya\":" + String(daya);
  payload += "}";

  return payload;
}

// =======================
// KIRIM DATA
// =======================
void kirimData() {
  if (!client.connected()) return;

  String data = generateJSON();

  Serial.println("📤 Kirim Data:");
  Serial.println(data);

  client.publish(topic, data.c_str());
}

// =======================
// SETUP
// =======================
void setup() {
  Serial.begin(115200);

  WiFi.mode(WIFI_STA);

  client.setServer(mqtt_server, mqtt_port);

  // Stabilitas tambahan
  client.setKeepAlive(60);
  client.setSocketTimeout(60);

  randomSeed(analogRead(0));
}

// =======================
// LOOP
// =======================
void loop() {
  connectWiFi();
  connectMQTT();

  client.loop();

  unsigned long now = millis();

  if (now - lastSend > interval) {
    lastSend = now;
    kirimData();
  }
}