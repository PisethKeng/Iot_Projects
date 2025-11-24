import network, socket, ure, time
from machine import Pin, PWM

# --- NEW: HTTP client for InfluxDB ---
import urequests

# --- Wi-Fi ---
WIFI_SSID = "Robotic WIFI"
WIFI_PASS = "rbtWIFI@2025i"


def wifi_connect():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        sta.connect(WIFI_SSID, WIFI_PASS)
        for _ in range(80):
            if sta.isconnected():
                break
            time.sleep(0.25)
    if not sta.isconnected():
        raise RuntimeError("WiFi connect failed")

    ip = sta.ifconfig()[0]
    # Old (shows IP): print("WiFi:", sta.ifconfig())
    print("WiFi: connected")  # No IP shown
    return ip

# --- InfluxDB config (LOCAL) ---
# 1. Find your Mac IP on Wi-Fi:
#    macOS Terminal: ipconfig getifaddr en0
# 2. Create DB in Influx: CREATE DATABASE motor_logs
# 3. Put your IP below:
INFLUX_URL = "http://10.30.0.153:8086/write?db=motor_logs&precision=s"  

def log_event(action, speed):
    """
    Send a single point to InfluxDB with:
      measurement: motor_events
      tag: action=<forward|backward|stop|speed>
      field: speed=<0..100>
      timestamp: current time (seconds)
    """
    # seconds since epoch; precision=s in URL
    ts = int(time.time())

    # InfluxDB line protocol:
    # measurement,tag=value field=value timestamp
    line = "motor_events,action={action} speed={speed}".format(
        action=action,
        speed=int(speed),
        ts=ts
    )

    print("Influx line:", line)

    try:
        resp = urequests.post(
            INFLUX_URL,
            data=line,
            headers={
                "Content-Type": "text/plain; charset=utf-8"
            },
        )
        print("Influx status:", resp.status_code)
        resp.close()
    except Exception as e:
        # Don't crash the web server if logging fails
        print("Influx error:", e)

# --- L298N pins ---
IN1 = Pin(26, Pin.OUT)
IN2 = Pin(27, Pin.OUT)
ENA = PWM(Pin(25), freq=1000)
PWM_MAX = 1023
_speed_pct = 70

def set_speed(pct):
    global _speed_pct
    pct = int(max(0, min(100, pct)))
    _speed_pct = pct
    ENA.duty(int(PWM_MAX * (_speed_pct / 100.0)))
    print("Speed:", _speed_pct, "%")

def motor_forward():
    set_speed(_speed_pct)
    IN1.on()
    IN2.off()
    print("Forward")
    # log to Influx
    log_event("forward", _speed_pct)

def motor_backward():
    set_speed(_speed_pct)
    IN1.off()
    IN2.on()
    print("Backward")
    # log to Influx
    log_event("backward", _speed_pct)

def motor_stop():
    IN1.off()
    IN2.off()
    ENA.duty(0)
    print("Stop")
    # log to Influx
    log_event("stop", 0)

# --- HTTP ---
HEAD_OK_TEXT = (
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: text/plain\r\n"
    "Access-Control-Allow-Origin: *\r\n"
    "Connection: close\r\n\r\n"
)

HEAD_OK_HTML = (
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: text/html\r\n"
    "Access-Control-Allow-Origin: *\r\n"
    "Connection: close\r\n\r\n"
)

HEAD_404 = (
    "HTTP/1.1 404 Not Found\r\n"
    "Content-Type: text/plain\r\n"
    "Access-Control-Allow-Origin: *\r\n"
    "Connection: close\r\n\r\nNot Found"
)

HOME_HTML = """<!doctype html><meta name=viewport content="width=device-width,initial-scale=1">
<h3>ESP32 Motor</h3>
<p>
  <a href="/forward"><button>Forward</button></a>
  <a href="/backward"><button>Backward</button></a>
  <a href="/stop"><button>Stop</button></a>
</p>
<p>
  <label>Speed:</label>
  <input id="spd" type="range" min="0" max="100" value="70"
    oninput="fetch('/speed?value='+this.value).then(r=>r.text()).then(console.log);">
</p>
"""

def route(path):
    if path == "/" or path.startswith("/index"):
        return HEAD_OK_HTML + HOME_HTML
    if path.startswith("/favicon.ico"):
        return HEAD_OK_TEXT
    if path.startswith("/forward"):
        motor_forward()
        return HEAD_OK_TEXT + "forward"
    if path.startswith("/backward"):
        motor_backward()
        return HEAD_OK_TEXT + "backward"
    if path.startswith("/stop"):
        motor_stop()
        return HEAD_OK_TEXT + "stop"
    if path.startswith("/speed"):
        m = ure.search(r"value=(\d+)", path)
        if m:
            v = int(m.group(1))
            set_speed(v)
            # log speed change as its own event
            log_event("speed", v)
            return HEAD_OK_TEXT + "speed=" + m.group(1)
        return HEAD_OK_TEXT + "speed?value=0..100"
    print("Unknown path:", path)
    return HEAD_404

def start_server(ip):
    addr = socket.getaddrinfo(ip, 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(3)
    # Old (shows IP): print("HTTP:", "http://%s/" % ip)
    print("HTTP server running")  # No IP shown

    while True:
        try:
            cl, _ = s.accept()
            cl.settimeout(2)
            try:
                req = cl.recv(1024)
                if not req:
                    cl.close()
                    continue

                try:
                    text = req.decode("utf-8", "ignore")
                except:
                    text = str(req)

                first = ""
                for ln in text.split("\r\n"):
                    if ln:
                        first = ln
                        break
                parts = first.split(" ")
                path = parts[1] if len(parts) >= 2 else "/"

                resp = route(path)
                cl.sendall(resp)
            except OSError as e:
                # errno 116 (ETIMEDOUT) is common on mobile; ignore
                if getattr(e, "errno", None) != 116:
                    print("Socket error:", e)
            except Exception as e:
                print("Handler error:", e)
            finally:
                try:
                    cl.close()
                except:
                    pass
        except Exception as e:
            print("Accept error:", e)
            time.sleep(0.1)

# --- main ---
if __name__ == "__main__":
    motor_stop()
    set_speed(_speed_pct)
    ip = wifi_connect()
    start_server(ip)
