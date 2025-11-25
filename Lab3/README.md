# LAB3 IOT 🌤️ IoT BMP280 → ThingsBoard Cloud (ESP32 + MicroPython)


This project demonstrates how to collect real-time temperature, pressure, and altitude data using a **BMP280** sensor connected to an **ESP32**, and publish those readings to **ThingsBoard Cloud** via MQTT.

## 📁 Project Structure

- **main.py** — connects to Wi-Fi and publishes BMP280 telemetry to ThingsBoard Cloud.  
- **mybmp280.py** — local BMP280 driver module (already imported and working).  
- **README.md** — project documentation.

---

## ⚙️ Hardware Requirements

| Component | Description |
|------------|--------------|
| ESP32 board | Any ESP32-based development board with MicroPython support |
| BMP280 sensor | Pressure & temperature sensor (I²C interface) |
| Jumper wires | For I²C connection |

---

## 🔌 Wiring (I²C)

| BMP280 Pin | ESP32 Pin |
|-------------|-----------|
| VCC | 3.3 V |
| GND | GND |
| SCL | GPIO 22 |
| SDA | GPIO 21 |

> **Note:** If your sensor uses I²C address `0x77`, change it in `main.py`.

---

## 🌐 Cloud Configuration (ThingsBoard)

1. Sign up or log in at [https://thingsboard.cloud](https://thingsboard.cloud)  
2. Navigate to **Devices → Add New Device**  
3. Open the device → copy its **Access Token**  
4. Use this token in the `TB_TOKEN` variable inside `main.py`  
5. MQTT endpoint:  
   - Host: `mqtt.thingsboard.cloud`  
   - Port: `1883`  
   - Topic: `v1/devices/me/telemetry`

---

## 💻 Software Setup

1. **Install MicroPython** on your ESP32 (if not already installed).  
2. Use **Thonny**, **mpremote**, or **ampy** to upload:
   - `main.py`
   - `mybmp280.py`
3. Edit `main.py`:
   ```python
   SSID = "Your Wi-Fi Name"
   PASS = "Your Wi-Fi Password"
   TB_TOKEN = b"Your_ThingsBoard_Access_Token"
