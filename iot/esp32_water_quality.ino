/* ClearWater - ESP32 MQTT sensor publisher
 * Hardware from project synopsis:
 * pH sensor, SEN0189/Gravity turbidity, Gravity TDS V1.0, DS18B20.
 * Calibrate sensor-specific conversion formulas before deployment.
 */
#include <WiFi.h>
#include <PubSubClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>

const char* WIFI_SSID = "YOUR_WIFI";
const char* WIFI_PASSWORD = "YOUR_PASSWORD";
const char* MQTT_HOST = "YOUR_MQTT_BROKER";
const int MQTT_PORT = 1883;
const char* MQTT_TOPIC = "water/wqm-01/readings";

const int PH_PIN = 34;
const int TURBIDITY_PIN = 35;
const int TDS_PIN = 32;
const int ONE_WIRE_PIN = 4;

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
OneWire oneWire(ONE_WIRE_PIN);
DallasTemperature tempSensor(&oneWire);

void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) delay(500);
}

void connectMQTT() {
  while (!mqtt.connected()) {
    mqtt.connect("WQM-01");
    delay(500);
  }
}

void setup() {
  Serial.begin(115200);
  tempSensor.begin();
  connectWiFi();
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();
  if (!mqtt.connected()) connectMQTT();
  mqtt.loop();

  // IMPORTANT: replace these conversions with your calibrated sensor formulas.
  float ph = analogRead(PH_PIN) * 14.0f / 4095.0f;
  float turbidity = analogRead(TURBIDITY_PIN) * 10.0f / 4095.0f;
  float tds = analogRead(TDS_PIN) * 1000.0f / 4095.0f;
  tempSensor.requestTemperatures();
  float temperature = tempSensor.getTempCByIndex(0);

  String payload = String("{\"nodeId\":\"WQM-01\",\"ph\":") + String(ph,2)
    + String(",\"turbidity\":") + String(turbidity,2)
    + String(",\"tds\":") + String(tds,1)
    + String(",\"temperature\":") + String(temperature,2) + String("}");

  mqtt.publish(MQTT_TOPIC, payload.c_str());
  delay(5000);
}
