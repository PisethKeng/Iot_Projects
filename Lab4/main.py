import network, time, random
from umqtt.simple import MQTTClient

SSID = "TP-LINK_56C612"
PASSWORD = "06941314"
BROKER = "test.mosquitto.org"
PORT = 1883
CLIENT_ID = b"esp32_random_1"
TOPIC = b"/aupp/esp32/random"
KEEPALIVE = 30

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), t0) > 20000:
                raise RuntimeError("Wi-Fi connect timeout")
            time.sleep(0.3)
    print("WiFi OK:", wlan.ifconfig())
    return wlan

def make_client():
    return MQTTClient(client_id=CLIENT_ID, server=BROKER, port=PORT, keepalive=KEEPALIVE)

def connect_mqtt(c):
    time.sleep(0.5)
    c.connect()
    print("MQTT connected")

def main():
    wifi_connect()
    client = make_client()
    while True:
        try:
            connect_mqtt(client)
            while True:
                value = random.randint(0, 100)
                msg = str(value)
                client.publish(TOPIC, msg)
                print("Sent:", msg)
                time.sleep(5)
        except OSError as e:
            print("MQTT error:", e)
            try:
                client.close()
            except:
                pass
            print("Retrying MQTT in 3s...")
            time.sleep(3)

main()
