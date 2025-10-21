# main.py — ESP32 + MicroPython → ThingsBoard Cloud (BMP280 telemetry)
import network, time, json
from umqtt.simple import MQTTClient
from machine import Pin, I2C
from mybmp280 import BMP280  # you're already providing this

# ===== Wi-Fi =====
SSID = "Robotic WIFI"
PASS = "rbtWIFI@2025"

# ===== ThingsBoard Cloud (MQTT 1883) =====
TB_HOST = "mqtt.thingsboard.cloud"
TB_PORT = 1883
TB_TOKEN = b"mfst7LzVuEWZtxVo2idQ"       # Device Access Token
TOPIC    = b"v1/devices/me/telemetry"    # Telemetry topic

# --- Wi-Fi connect ---
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    wlan.connect(SSID, PASS)
    t0 = time.ticks_ms()
    while not wlan.isconnected():
        if time.ticks_diff(time.ticks_ms(), t0) > 15000:
            raise RuntimeError("Wi-Fi connection timeout")
        time.sleep(0.2)
print("Wi-Fi:", wlan.ifconfig())

# --- MQTT connect (username = token, empty password) ---
client = MQTTClient(
    client_id=b"esp32-bmp280",
    server=TB_HOST,
    port=TB_PORT,
    user=TB_TOKEN,
    password=b"",
    keepalive=30,
    ssl=False
)
client.connect()
print("MQTT: connected to", TB_HOST, TB_PORT)

# --- BMP280 init (your exact wiring) ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
bmp = BMP280(i2c, addr=0x76)  # change to 0x77 if needed

# --- Read + Publish loop ---
while True:
    temp_c = bmp.temperature
    press_hpa = bmp.pressure / 100.0
    alt_m = bmp.altitude

    # Local serial debug (kept from your test)
    print("Temperature (°C):", temp_c)
    print("Pressure (hPa):", press_hpa)
    print("Altitude (m):", alt_m)
    print("------------------")

    # Telemetry payload → ThingsBoard
    payload = json.dumps({
        "temperature": round(temp_c, 2),
        "pressure": round(press_hpa, 2),
        "altitude": round(alt_m, 2)
    }).encode("utf-8")

    client.publish(TOPIC, payload)
    time.sleep(5)

