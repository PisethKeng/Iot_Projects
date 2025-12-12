# esp32_thresholdbot.py  (MicroPython)

import time
import network
import urequests as requests
import machine
import dht

# ==== USER SETTINGS ====
WIFI_SSID = env.get("WIFI_SSID", "")
WIFI_PSK  = env.get("WIFI_PSK", "")

BOT_TOKEN = env.get("BOT_TOKEN", "")    # <- regenerate for safety
CHAT_ID   = env.get("CHAT_ID", "")                        # group chat id (negative)

DHT_PIN = 4                                    # DHT11 data pin (switch to DHT22 if needed)
RELAY_PIN = 2                                  # Relay pin

CHECK_INTERVAL = 5                             # seconds between loops
TEMP_THRESHOLD = 30.0                          # default °C (can change at runtime with /setth)
# =======================

# --- Relay setup ---
relay = machine.Pin(RELAY_PIN, machine.Pin.OUT)
relay.value(0)                                  # OFF at start
relay_forced_on = False                         # set True after /on; cleared on auto/off or /off

def relay_on():
    global relay_forced_on
    relay.value(1)
    relay_forced_on = True
    print("[RELAY] ON")

def relay_off():
    global relay_forced_on
    relay.value(0)
    relay_forced_on = False
    print("[RELAY] OFF")

def relay_is_on():
    return relay.value() == 1

# --- Wi-Fi ---
def wifi_connect(ssid, psk, timeout=20):
    sta = network.WLAN(network.STA_IF)
    if not sta.active():
        sta.active(True)
    if not sta.isconnected():
        print("Connecting to Wi-Fi:", ssid)
        sta.connect(ssid, psk)
        t0 = time.ticks_ms()
        while not sta.isconnected():
            if time.ticks_diff(time.ticks_ms(), t0) > timeout * 1000:
                raise OSError("Wi-Fi timed out")
            time.sleep(0.3)
    print("Wi-Fi OK:", sta.ifconfig())

def wifi_ensure():
    sta = network.WLAN(network.STA_IF)
    if not sta.isconnected():
        try:
            wifi_connect(WIFI_SSID, WIFI_PSK)
        except Exception as e:
            print("wifi_ensure error:", e)

# --- Telegram helpers (MicroPython-friendly) ---
TG_BASE = "https://api.telegram.org/bot{}".format(BOT_TOKEN)

def _urlencode(s):
    try:
        import urllib.parse as up
        return up.quote(str(s), safe='')
    except:
        return str(s).replace('%','%25').replace(' ','%20').replace('\n','%0A')

def send_message(chat_id, text):
    try:
        url = TG_BASE + "/sendMessage?chat_id={}&text={}".format(chat_id, _urlencode(text))
        r = requests.get(url)   # GET is robust on urequests
        status = r.status_code
        body = r.text
        r.close()
        if status != 200:
            print("send_message failed:", status, body)
            return False
        print("send_message OK")
        return True
    except Exception as e:
        print("send_message error:", e)
        return False

def get_updates(offset=None, timeout=5):
    try:
        url = TG_BASE + "/getUpdates?timeout={}".format(timeout)
        if offset:
            url += "&offset={}".format(offset)
        r = requests.get(url)
        status = r.status_code
        txt = r.text
        try:
            data = r.json()
        except:
            data = {}
        r.close()
        if status != 200:
            print("get_updates HTTP", status, txt)
        return data
    except Exception as e:
        print("get_updates error:", e)
        return {}

# --- Commands ---
def handle_cmd(chat_id, text, current_temp):
    global TEMP_THRESHOLD
    t = (text or "").strip()
    tl = t.lower()

    # allow /cmd@BotName in groups
    if '@' in tl:
        tl = tl.split('@', 1)[0]

    if tl in ("/on", "on"):
        # Alerts will stop because condition below only sends when relay is OFF
        if current_temp >= TEMP_THRESHOLD:
            relay_on()
            send_message(chat_id, "Relay: ON (Temp {:.2f}°C)".format(current_temp))
        else:
            send_message(chat_id, "Temp {:.2f}°C < {:.2f}°C → Relay stays OFF".format(current_temp, TEMP_THRESHOLD))

    elif tl in ("/off", "off"):
        relay_off()
        send_message(chat_id, "Relay: OFF")

    elif tl in ("/status", "status"):
        send_message(chat_id,
            "Status:\nTemp: {:.2f}°C\nRelay: {}\nThreshold: {:.2f}°C"
            .format(current_temp, "ON" if relay_is_on() else "OFF", TEMP_THRESHOLD))

    elif tl.startswith("/setth"):
        # Usage: /setth 27.5
        parts = t.split()
        if len(parts) == 2:
            try:
                new_th = float(parts[1])
                TEMP_THRESHOLD = new_th
                send_message(chat_id, "Threshold set to {:.2f}°C".format(TEMP_THRESHOLD))
                print("[THRESH] updated to {:.2f}°C".format(TEMP_THRESHOLD))
            except:
                send_message(chat_id, "Send like: /setth 27.5")
        else:
            send_message(chat_id, "Send like: /setth 27.5")

    elif tl in ("/getth", "/threshold"):
        send_message(chat_id, "Current threshold: {:.2f}°C".format(TEMP_THRESHOLD))

    elif tl in ("/help", "/start", "help"):
        send_message(chat_id,
            "Commands:\n"
            "/status  – show Temp/Relay/Threshold\n"
            "/on      – turn relay ON (only if Temp ≥ threshold)\n"
            "/off     – turn relay OFF\n"
            "/setth X – set threshold to X °C (e.g., 27.5)\n"
            "/getth   – show current threshold")

# --- Sensor (DHT11 by default; switch to DHT22 if that’s what you wired) ---
sensor = dht.DHT11(machine.Pin(DHT_PIN))
# For DHT22 use:
# sensor = dht.DHT22(machine.Pin(DHT_PIN))

def read_dht():
    for _ in range(3):
        try:
            sensor.measure()
            t = sensor.temperature()
            h = sensor.humidity()
            if t is not None and h is not None:
                return round(t, 2), round(h, 2)
        except Exception as e:
            print("DHT error:", e)
        time.sleep(1)
    raise OSError("DHT read failed")

# --- Boot test message ---
def send_test_message():
    send_message(CHAT_ID, "🤖 ESP32 ThresholdBot online. Threshold = {:.2f}°C".format(TEMP_THRESHOLD))

# --- Main loop (Task-4 rules) ---
def main():
    wifi_connect(WIFI_SSID, WIFI_PSK)
    send_test_message()

    update_offset = None
    last_temp = None
    auto_notice_sent = False  # ensures one-time “auto-OFF” notice

    while True:
        try:
            wifi_ensure()

            # 1) Read & print
            try:
                temp, hum = read_dht()
                print("[SERIAL] Temp: {:.2f}°C | Hum: {:.2f}% | Relay: {} | TH={:.2f}°C"
                      .format(temp, hum, "ON" if relay_is_on() else "OFF", TEMP_THRESHOLD))
            except Exception as e:
                print("[SERIAL] Sensor read failed this cycle:", e)
                time.sleep(CHECK_INTERVAL)
                continue

            # ===== Task-4 logic =====
            # No messages while T < threshold (implicit by these conditions)

            # If T ≥ TH and relay OFF → alert EVERY loop (5 s) until /on
            if temp >= TEMP_THRESHOLD and not relay_is_on():
                send_message(
                    CHAT_ID,
                    "⚠️ Temp {:.2f}°C ≥ {:.2f}°C. Relay is OFF. Send /on to activate."
                    .format(temp, TEMP_THRESHOLD)
                )
                auto_notice_sent = False  # we're in hot state; reset

            # After /on, stop alerts. When T < TH → auto-OFF + one-time notice
            if relay_is_on() and relay_forced_on and temp < TEMP_THRESHOLD:
                relay_off()
                send_message(
                    CHAT_ID,
                    "✅ Temp back below {:.2f}°C (now {:.2f}°C). Relay turned OFF automatically."
                    .format(TEMP_THRESHOLD, temp)
                )
                auto_notice_sent = True

            # Optional: if relay already OFF when cooling below TH, send a single “back to normal” info
            if (last_temp is not None and last_temp >= TEMP_THRESHOLD and temp < TEMP_THRESHOLD
                and not relay_is_on() and not auto_notice_sent):
                send_message(CHAT_ID, "ℹ️ Temp back below {:.2f}°C (now {:.2f}°C)."
                                       .format(TEMP_THRESHOLD, temp))
                auto_notice_sent = True
            # ========================

            last_temp = temp

            # 2) Poll Telegram for commands
            updates = get_updates(offset=update_offset)
            if "result" in updates:
                for upd in updates["result"]:
                    update_offset = upd["update_id"] + 1
                    if "message" in upd and "text" in upd["message"]:
                        cid = upd["message"]["chat"]["id"]
                        text = upd["message"]["text"]
                        handle_cmd(cid, text, temp)

        except Exception as e:
            print("[LOOP] error:", e)

        time.sleep(CHECK_INTERVAL)

# ---- Run ----
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        relay_off()
        print("Stopped.")
