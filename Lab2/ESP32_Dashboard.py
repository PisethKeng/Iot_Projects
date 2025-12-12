
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
    # --- START OF MODIFIED CSS ---
    return """<!DOCTYPE html>
<html>
<head>
    <title>ESP32 Sensor Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      body {
        font-family: 'Montserrat', sans-serif; /* Changed font */
        background: linear-gradient(to right, #134e5e 0%, #71b280 100%);
        color: #e0e0e0; /* Lighter text for dark background */
        text-align: center;
        margin: 0;
        padding: 0;
      }
      h2 {
        background-color: rgba(255, 252, 243, 0.15); /* Slightly transparent white */
        padding: 20px; /* Increased padding */
        margin: 0;
        font-size: 2.5em; /* Larger heading */
        color: #ffffff; /* White heading text */
        border-bottom: 2px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 2px 10px rgba(0,0,0,0.3); /* Subtle shadow */
      }
      .container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        margin: 25px auto; /* Adjusted margin */
        max-width: 900px; /* Wider container */
      }
      .card {
        background-color: rgba(255, 255, 255, 0.1); /* Lighter transparent white for cards */
        border-radius: 15px; /* More rounded corners */
        padding: 25px; /* Increased padding */
        margin: 12px; /* Adjusted margin */
        min-width: 160px; /* Slightly larger min-width */
        flex: 1 1 200px; /* Flex basis adjusted */
        box-shadow: 0 6px 15px rgba(0,0,0,0.4); /* Stronger shadow for depth */
        transition: transform 0.3s ease-in-out, background-color 0.3s ease-in-out; /* Smooth transitions */
        backdrop-filter: blur(5px); /* Frosted glass effect */
        border: 1px solid rgba(255, 255, 255, 0.2); /* Subtle border */
      }
      .card:hover {
          transform: translateY(-8px) scale(1.03); /* Lift and scale on hover */
          background-color: rgba(255, 255, 255, 0.15); /* Slightly more opaque on hover */
      }
      .card h3 {
          margin: 10px 0;
          color: #ffffff; /* White heading for cards */
          font-size: 1.5em;
      }
      .card p {
          font-size: 1.8em; /* Larger sensor values */
          font-weight: bold;
          color: #ffee00; /* Bright yellow for sensor readings */
          margin: 15px 0;
      }
      button {
        padding: 12px 25px;
        margin: 6px; /* Adjusted margin */
        border: none;
        border-radius: 25px; /* Pill-shaped buttons */
        cursor: pointer;
        font-size: 1.05em; /* Slightly larger font */
        color: #ffffff;
        transition: background-color 0.3s ease, transform 0.2s ease;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2); /* Button shadow */
      }
      button:hover {
          opacity: 0.95; /* Slightly less opaque */
          transform: translateY(-2px); /* Lift button on hover */
      }
      .led-on { background-color: #28a745; } /* Green */
      .led-off { background-color: #dc3545; } /* Red */
      .lcd { background-color: #007bff; } /* Blue */
      .sensor-btn { background-color: #ffc107; color: #333; } /* Yellow-orange, darker text */
      .both-sensors { background-color: #6f42c1; } /* Purple */
      input[type=text] {
        padding: 12px; /* Increased padding */
        width: 70%; /* Wider input field */
        border-radius: 10px; /* Rounded corners */
        border: 1px solid #cccccc; /* Subtle border */
        margin: 10px 0;
        font-size: 1.0em;
        background-color: rgba(255, 255, 255, 0.9); /* Slightly transparent white */
        color: #333;
      }
      input[type=text]::placeholder {
          color: #666;
      }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet"> <script>
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
    <h2>ESP32 Sensor Dashboard</h2>
    <div class="container">
      <div class="card">
        <h3>Distance</h3>
        <p id="distance">--</p>
        <button class="sensor-btn" onclick="fetch('/show_distance')">Show Distance</button>
      </div>
      <div class="card">
        <h3>Temperature</h3>
        <p id="temperature">--</p>
        <button class="sensor-btn" onclick="fetch('/show_temperature')">Show Temperature</button>
      </div>
      <div class="card">
        <h3>LED</h3>
        <p id="led">--</p>
        <button class="led-on" onclick="fetch('/led_on')">LED ON</button>
        <button class="led-off" onclick="fetch('/led_off')">LED OFF</button>
      </div>
      <div class="card">
        <h3>LCD Controls</h3>
        <p id="lcd">--</p>
        <button class="both-sensors" onclick="fetch('/show_both_sensors')">Show Both</button>
        <button class="lcd" onclick="fetch('/hide_lcd')">Hide LCD</button>
      </div>
    </div>

    <div class="card" style="max-width:400px; margin:auto;">
      <h3>Custom LCD Message</h3>
      <input type="text" id="lcdInput" placeholder="Enter text for LCD">
      <button class="lcd" onclick="sendLCDText()">Send</button>
    </div>
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
