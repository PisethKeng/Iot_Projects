# 🌐 ESP32 → MQTT → Node-RED → InfluxDB → Grafana Dashboard

This project demonstrates a complete **IoT data pipeline** using an **ESP32** running **MicroPython** to publish random sensor values via **MQTT** to **Node-RED**, which stores the data in **InfluxDB** and visualizes it in **Grafana**.

---

## 🧭 Table of Contents

* [Architecture Overview](#architecture-overview)
* [Prerequisites](#prerequisites)
* [1️⃣ ESP32 Setup (MicroPython)](#1️⃣-esp32-setup-micropython)
* [2️⃣ Node-RED Setup (MQTT → InfluxDB)](#2️⃣-node-red-setup-mqtt--influxdb)
* [3️⃣ InfluxDB Installation & Configuration](#3️⃣-influxdb-installation--configuration)
* [4️⃣ Grafana Dashboard Setup](#4️⃣-grafana-dashboard-setup)
* [5️⃣ Verification](#5️⃣-verification)
* [6️⃣ Troubleshooting](#6️⃣-troubleshooting)

---

## 🧩 Architecture Overview

**Data Flow:**

```
ESP32 (MicroPython)
    ↓
MQTT Broker (test.mosquitto.org:1883)
    ↓
Node-RED (MQTT In → Function → InfluxDB Out)
    ↓
InfluxDB (Measurement: random, Field: value, Tag: device)
    ↓
Grafana Dashboard (InfluxQL Queries + Auto Refresh)
```

*You can insert your architecture diagram here.*

---

## ⚙️ Prerequisites

### Hardware

* ESP32 board (any variant supporting MicroPython)

### Software

* [MicroPython](https://micropython.org/download/esp32/) — flashed onto ESP32
* [Node-RED](https://nodered.org/) — local automation server ([http://localhost:1880](http://localhost:1880))
* [InfluxDB 1.x](https://docs.influxdata.com/influxdb/v1.8/introduction/) — time-series database ([http://127.0.0.1:8086](http://127.0.0.1:8086))
* [Grafana](https://grafana.com/grafana/download) — visualization dashboard ([http://localhost:3000](http://localhost:3000))

### Optional

* [MQTT Explorer](https://mqtt-explorer.com/) — inspect MQTT topics easily

---

## 🛠️ 1️⃣ ESP32 Setup (MicroPython)

1. Flash MicroPython firmware onto your ESP32.
2. Upload and run the following code using **Thonny**, **mpremote**, or **ampy**:

```python
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
```

✅ Publishes random integers to `/aupp/esp32/random`.


<img width="1728" height="1117" alt="Screenshot 2025-10-23 at 11 55 39 PM" src="https://github.com/user-attachments/assets/6c3138cf-e90e-4d34-910f-ddfcaacf2cbc" />

---

## 🧩 2️⃣ Node-RED Setup (MQTT → InfluxDB)

1. Start Node-RED:

   ```bash
   node-red
   ```

   Open [http://localhost:1880](http://localhost:1880).

2. Create a flow using:

   * **mqtt in**
   * **function**
   * **influxdb out**

3. Configure **MQTT In** node:

   * Server: `test.mosquitto.org`
   * Port: `1883`
   * Topic: `/aupp/esp32/random`

4. Add a **Function** node with:

   ```js
   msg.measurement = "random";
   msg.payload = { value: Number(msg.payload) };
   return msg;
   ```
   
<img width="1728" height="1117" alt="Screenshot 2025-10-23 at 11 55 31 PM" src="https://github.com/user-attachments/assets/d89e0976-576a-4a67-b887-dca854800399" />

   

5. Configure **InfluxDB Out**:

   * Database: `aupp_lab`
   * Measurement: `random`

6. Deploy and verify using **Debug Node** to ensure messages arrive correctly.

---

## 🗄️ 3️⃣ InfluxDB Installation & Configuration

### Installation (Windows Example)

```bash
wget https://download.influxdata.com/influxdb/releases/v1.12.2/influxdb-1.12.2-windows.zip
Expand-Archive .\influxdb-1.12.2-windows.zip -DestinationPath 'C:\Program Files\InfluxData\influxdb\'
cd "C:\Program Files\InfluxData\influxdb"
.\influxd.exe
```

### Create Database

In a new PowerShell window:

```bash
cd "C:\Program Files\InfluxData\influxdb"
.\influx.exe -host 127.0.0.1
CREATE DATABASE aupp_lab;
USE aupp_lab;
SELECT * FROM random ORDER BY time DESC LIMIT 5;
```

---

## 📊 4️⃣ Grafana Dashboard Setup

1. Open Grafana at [http://localhost:3000](http://localhost:3000)
   Default credentials:

   ```
   Username: admin
   Password: admin
   ```

2. Go to ⚙️ → **Data Sources** → **Add Data Source** → select **InfluxDB**

3. Configure:

   | Setting         | Value                                          |
   | --------------- | ---------------------------------------------- |
   | Query Language  | InfluxQL                                       |
   | URL             | [http://127.0.0.1:8086](http://127.0.0.1:8086) |
   | Database        | aupp_lab                                       |
   | User / Password | (leave blank if not configured)                |
   | Version         | 1.8+                                           |

4. Create a new dashboard:

   * Click **+ → Dashboard → Add new panel**
   * Select your InfluxDB data source
   * Query measurement: `random`
   * Field: `value`
   * Enable **Auto Refresh** (e.g., every 5 seconds)



<img width="1728" height="1117" alt="Screenshot 2025-10-23 at 11 55 23 PM" src="https://github.com/user-attachments/assets/fb2d4101-0694-4f9e-8b60-c85312bc959f" />


---

## ✅ 5️⃣ Verification

Once everything is connected:

* ESP32 publishes random values every 5 seconds.
* Node-RED receives data via MQTT.
* InfluxDB stores measurements.
* Grafana visualizes live updates.

---

## 🧰 6️⃣ Troubleshooting

| Issue                         | Possible Cause                             | Solution                            |
| ----------------------------- | ------------------------------------------ | ----------------------------------- |
| ESP32 not connecting to Wi-Fi | Wrong SSID/PASSWORD                        | Double-check credentials            |
| Node-RED not receiving data   | Wrong MQTT topic or broker                 | Verify broker: `test.mosquitto.org` |
| No data in InfluxDB           | Missing Function node or wrong measurement | Recheck Node-RED flow               |
| Grafana shows no data         | Wrong query or data source                 | Ensure InfluxQL and DB name match   |

---

## 🧑‍💻 Author

**[Group 9]**
💡 *Feel free to fork, modify, or expand this project for your own IoT experiments.*

---

## 📸 Image Placeholders

* Node-RED flow
* MQTT configuration
* InfluxDB CLI output
* Grafana dashboard view

> *Add your screenshots here once your setup is complete.*
