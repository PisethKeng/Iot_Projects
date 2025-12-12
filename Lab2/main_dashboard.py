
try:
    import usocket as socket
except:
    import socket

import network
from machine import Pin, I2C, time_pulse_us
from time import sleep_us, sleep
import dht
import esp
import gc
import json
from machine_i2c_lcd import I2cLcd

esp.osdebug(None)
gc.collect()

# -------- WiFi ----------
SSID = "Robotic WIFI"
PASSWORD = "rbtWIFI@2025"

station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(SSID, PASSWORD)
while not station.isconnected():
    print(".", end="")
    sleep(0.5)

print("\n✅ WiFi connected, IP:", station.ifconfig()[0])

# -------- Hardware ----------
sensor = dht.DHT22(Pin(4))
led = Pin(2, Pin.OUT)

# I2C LCD
i2c = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
I2C_ADDR = 0x27
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)

def send_to_lcd(row, text):
    lcd.move_to(0, row - 1)
    lcd.putstr(" " * 16)
    lcd.move_to(0, row - 1)
    lcd.putstr(text[:16])

# -------- Ultrasonic ----------
TRIG = Pin(27, Pin.OUT)
ECHO = Pin(26, Pin.IN)

def distance_cm():
    TRIG.off()
    sleep_us(2)
    TRIG.on()
    sleep_us(10)
    TRIG.off()
    t = time_pulse_us(ECHO, 1, 30000)
    if t < 0:
        return None
    return (t * 0.0343) / 2.0

# -------- Temperature ----------
def read_temperature():
    try:
        sensor.measure()
        return sensor.temperature()
    except OSError:
        return None
 # -------- Web Page ----------
def web_page():
    return """<!DOCTYPE html>
<html>
<head>
  <title>ESP32 Sensor Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <style>
    :root{
      --glass: rgba(255,255,255,.12);
      --glass2: rgba(255,255,255,.18);
      --stroke: rgba(255,255,255,.25);
      --txt: #f2f5f4;
      --muted: #cfd8d3;
      --warn: #ffd84d;
      --shadow: 0 16px 40px rgba(0,0,0,.45);
      --shadow2: 0 10px 25px rgba(0,0,0,.35);
    }

    body{
      font-family: 'Montserrat', sans-serif;
      background: linear-gradient(to right, #134e5e 0%, #71b280 100%);
      color: var(--txt);
      margin: 0;
      padding: 0;
    }

    /* Top bar */
    header{
      padding: 18px 16px;
      background: rgba(0,0,0,.25);
      backdrop-filter: blur(8px);
      border-bottom: 1px solid var(--stroke);
      box-shadow: 0 4px 22px rgba(0,0,0,.35);
    }
    header h2{
      margin: 0;
      text-align: left;
      font-size: 1.9em;
      letter-spacing: .5px;
      font-weight: 700;
    }
    header p{
      margin: 6px 0 0;
      text-align: left;
      color: var(--muted);
      font-size: .95em;
    }

    /* Page layout */
    .wrap{
      max-width: 1100px;
      margin: 26px auto;
      padding: 0 14px 26px;
      display: grid;
      grid-template-columns: 1.2fr .8fr;
      gap: 18px;
    }

    /* Dashboard grid */
    .dashboard{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
      align-content: start;
    }

    /* Cards */
    .card{
      background: var(--glass);
      border: 1px solid var(--stroke);
      border-radius: 18px;
      padding: 18px;
      backdrop-filter: blur(10px);
      box-shadow: var(--shadow2);
      transition: transform .25s ease, background-color .25s ease, box-shadow .25s ease;
    }
    .card:hover{
      transform: translateY(-6px);
      background: var(--glass2);
      box-shadow: var(--shadow);
    }

    .card h3{
      margin: 0 0 10px;
      font-size: 1.2em;
      font-weight: 700;
    }

    .sub{
      margin: 0 0 10px;
      color: var(--muted);
      font-size: .92em;
      line-height: 1.35;
    }

    /* Readout row */
    .readout{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 10px;
      padding: 10px 12px;
      border-radius: 14px;
      border: 1px solid rgba(255,255,255,.18);
      background: rgba(0,0,0,.18);
      margin: 10px 0 14px;
    }
    .value{
      font-size: 1.8em;
      font-weight: 800;
      color: var(--warn);
    }
    .tag{
      font-size: .8em;
      color: var(--muted);
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,.18);
      background: rgba(255,255,255,.06);
      white-space: nowrap;
    }

    /* Buttons */
    .actions{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: center;
    }

    button{
      border: none;
      cursor: pointer;
      padding: 11px 16px;
      border-radius: 999px;
      font-weight: 700;
      font-size: .98em;
      transition: transform .2s ease, filter .2s ease;
      box-shadow: 0 4px 14px rgba(0,0,0,.25);
    }
    button:hover{
      transform: translateY(-2px);
      filter: brightness(1.08);
    }

    .led-on{ background: linear-gradient(to right, #1d976c, #93f9b9); color: #083b26; }
    .led-off{ background: linear-gradient(to right, #cb2d3e, #ef473a); color: #fff; }
    .lcd{ background: linear-gradient(to right, #396afc, #2948ff); color: #fff; }
    .sensor-btn{ background: linear-gradient(to right, #f7971e, #ffd200); color: #2b2b2b; }
    .both-sensors{ background: linear-gradient(to right, #0f2027, #2c5364, #1c7c54); color: #fff; }

    /* Side panel */
    .side{
      display: grid;
      gap: 18px;
      align-content: start;
    }

    input[type=text]{
      width: 100%;
      padding: 12px 14px;
      border-radius: 12px;
      border: none;
      outline: none;
      background: rgba(255,255,255,.95);
      color: #333;
      font-size: 1em;
      box-shadow: inset 0 2px 6px rgba(0,0,0,.18);
    }
    input[type=text]::placeholder{ color: #777; }

    /* Make LED status look like a pill */
    #led.led-on, #led.led-off{
      color: #fff;
      font-size: .95em;
      font-weight: 800;
      padding: 6px 12px;
      border-radius: 999px;
      display: inline-block;
      min-width: 64px;
      text-align: center;
      box-shadow: 0 6px 18px rgba(0,0,0,.25);
    }

    footer{
      max-width: 1100px;
      margin: 0 auto 26px;
      padding: 0 14px;
      color: rgba(255,255,255,.75);
      font-size: .9em;
      text-align: center;
    }

    /* Responsive */
    @media (max-width: 900px){
      .wrap{ grid-template-columns: 1fr; }
      header h2, header p{ text-align: center; }
      .dashboard{ grid-template-columns: 1fr; }
    }
  </style>

  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">

  <script>
    async function fetchData() {
      let r = await fetch('/data');
      let d = await r.json();
      document.getElementById("distance").innerText = d.distance + " cm";
      document.getElementById("temperature").innerText = d.temperature + " C";
      document.getElementById("led").innerText = d.ledState;
      document.getElementById("led").className = d.ledState === "ON" ? "led-on" : "led-off";
      document.getElementById("lcd").innerText = d.lcdStatus;
    }
    setInterval(fetchData, 2000);

    async function sendLCDText() {
      let msg = document.getElementById("lcdInput").value;
      if (msg.trim() !== "") {
        await fetch("/lcd_text?msg=" + encodeURIComponent(msg));
        document.getElementById("lcdInput").value = "";
        alert("Text sent to LCD!");
      }
    }
  </script>
</head>

<body onload="fetchData()">
  <header>
    <h2>ESP32 Forest Console</h2>
    <p>Live sensor snapshots • Control center • LCD messaging</p>
  </header>

  <main class="wrap">
    <!-- LEFT: Dashboard grid -->
    <section class="dashboard">
      <div class="card">
        <h3>Ultrasonic Range</h3>
        <p class="sub">Distance reading from the sensor.</p>
        <div class="readout">
          <span class="value" id="distance">--</span>
          <span class="tag">cm</span>
        </div>
        <div class="actions">
          <button class="sensor-btn" onclick="fetch('/show_distance')">Show on LCD</button>
        </div>
      </div>

      <div class="card">
        <h3>Temperature</h3>
        <p class="sub">Current temperature output.</p>
        <div class="readout">
          <span class="value" id="temperature">--</span>
          <span class="tag">°C</span>
        </div>
        <div class="actions">
          <button class="sensor-btn" onclick="fetch('/show_temperature')">Show on LCD</button>
        </div>
      </div>

      <div class="card">
        <h3>LED Control</h3>
        <p class="sub">Toggle the onboard LED state.</p>
        <div class="readout" style="justify-content:center;">
          <span id="led">--</span>
        </div>
        <div class="actions">
          <button class="led-on" onclick="fetch('/led_on')">Turn ON</button>
          <button class="led-off" onclick="fetch('/led_off')">Turn OFF</button>
        </div>
      </div>

      <div class="card">
        <h3>LCD Panel</h3>
        <p class="sub">Display sensor data or hide the screen.</p>
        <div class="readout">
          <span class="value" id="lcd">--</span>
          <span class="tag">status</span>
        </div>
        <div class="actions">
          <button class="both-sensors" onclick="fetch('/show_both_sensors')">Show Both</button>
          <button class="lcd" onclick="fetch('/hide_lcd')">Hide LCD</button>
        </div>
      </div>
    </section>

    <!-- RIGHT: Side panel -->
    <aside class="side">
      <div class="card">
        <h3>Custom LCD Message</h3>
        <p class="sub">Send your own text to the LCD display.</p>
        <input type="text" id="lcdInput" placeholder="Type message...">
        <div style="height:12px;"></div>
        <div class="actions">
          <button class="lcd" onclick="sendLCDText()">Send Message</button>
        </div>
      </div>

      <div class="card">
        <h3>Quick Tips</h3>
        <p class="sub">
          • Readings refresh every 2 seconds.<br>
          • “Show on LCD” pushes the value to the screen.<br>
          • Use short messages for best LCD fit.
        </p>
      </div>
    </aside>
  </main>

  <footer>
    ESP32 Dashboard • Forest UI Theme
  </footer>
</body>
</html>"""    
      
    # --- END OF MODIFIED CSS ---

# -------- Web Server ----------
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(5)
print("🌐 Web server running on http://%s/" % station.ifconfig()[0])

lcd_display_mode = "none"

while True:
    cl, addr = s.accept()
    try:
        req = cl.recv(1024).decode()
        path = req.split(" ")[1]
        print("➡️ Request:", path)

        dist_val = distance_cm()
        temp_val = read_temperature()

        if path == "/data":
            response_data = {
                "distance": f"{dist_val:.1f}" if dist_val is not None else "--",
                "temperature": f"{temp_val:.1f}" if temp_val is not None else "--",
                "ledState": "ON" if led.value() else "OFF",
                "lcdStatus": "SHOWING" if lcd_display_mode != "none" else "HIDDEN"
            }
            cl.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n" +
                    json.dumps(response_data))

        elif path == "/led_on":
            led.on()
            cl.send("HTTP/1.1 200 OK\r\n\r\n")

        elif path == "/led_off":
            led.off()
            cl.send("HTTP/1.1 200 OK\r\n\r\n")

        elif path == "/show_distance":
            lcd_display_mode = "distance"
            lcd.clear()
            if dist_val is not None:
                send_to_lcd(1, "Distance: %.1f cm" % dist_val)
            cl.send("HTTP/1.1 200 OK\r\n\r\n")

        elif path == "/show_temperature":
            lcd_display_mode = "temperature"
            lcd.clear()
            if temp_val is not None:
                send_to_lcd(1, "Temp: %.1f C" % temp_val)
            cl.send("HTTP/1.1 200 OK\r\n\r\n")

        elif path == "/show_both_sensors":
            lcd_display_mode = "sensors"
            lcd.clear()
            cl.send("HTTP/1.1 200 OK\r\n\r\n")

        elif path == "/hide_lcd":
            lcd_display_mode = "none"
            lcd.clear()
            cl.send("HTTP/1.1 200 OK\r\n\r\n")

        elif path.startswith("/lcd_text?msg="):
            try:
                msg = path.split("=", 1)[1]
                msg = msg.replace("%20", " ")
                lcd_display_mode = "custom"
                lcd.clear()
                send_to_lcd(1, msg[:16])
                if len(msg) > 16:
                    send_to_lcd(2, msg[16:32])
                cl.send("HTTP/1.1 200 OK\r\n\r\n")
            except Exception as e:
                print("LCD text error:", e)
                cl.send("HTTP/1.1 400 Bad Request\r\n\r\n")

        else:
            cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" +
                    web_page())

    except Exception as e:
        print("⚠️ Error:", e)
    finally:
        cl.close()

    # Auto-update LCD
    if lcd_display_mode == "distance" and dist_val is not None:
        send_to_lcd(1, "Distance: %.1f cm" % dist_val)
    elif lcd_display_mode == "temperature" and temp_val is not None:
        send_to_lcd(1, "Temp: %.1f C" % temp_val)
    elif lcd_display_mode == "sensors":
        # Clear both rows before updating to prevent artifacts
        lcd.clear()
        if dist_val is not None:
            send_to_lcd(1, "Dist: %.1f cm" % dist_val)
        if temp_val is not None:
            send_to_lcd(2, "Temp: %.1f C" % temp_val)
    elif lcd_display_mode == "custom":
        pass
    else:
        lcd.clear()
