
# 🚗 Smart Parking System (ESP32 + MicroPython)

A fully functional **IoT Smart Parking System** built using **ESP32** and **MicroPython**.  
This project detects parking slot availability using **IR sensors**, manages entry/exit with an **ultrasonic gate sensor** and **servo motor**, displays slot data on a **16x2 I2C LCD**, provides a **real-time web dashboard**, and sends **Telegram receipts** when cars exit.

---

## 🔍 Overview

This system automates a small parking lot with **3 vehicle slots**.  
It monitors occupancy, opens the entry gate when a car approaches, calculates parking fees based on duration, and notifies the user via Telegram upon vehicle exit.

All data (slots, status, history) is served locally through a **built-in ESP32 web server** with an **auto-refresh dashboard**.

---

## ✨ Features

- **3 Smart Parking Slots** – Detected via IR sensors with auto-ID assignment  
- **Ultrasonic Sensor (Gate Trigger)** – Detects vehicles approaching entry  
- **Servo Motor** – Controls automatic gate open/close  
- **16x2 I2C LCD Display** – Shows available slots in real-time  
- **Web Dashboard** – Live status (JSON & HTML view), responsive design  
- **Telegram Notifications** – Sends digital parking receipts on exit  
- **NTP Time Sync** – Ensures accurate timestamps (UTC+7)  
- **uasyncio Concurrency** – Smooth multitasking for sensors, server, and updates  
- **Dual Wi-Fi Mode** – Connects to local network or opens fallback Access Point  

---

## 🧠 System Architecture


---

## ⚙️ Hardware Requirements

| Component             | Quantity | Description / Pin Used            |
|-----------------------|-----------|-----------------------------------|
| ESP32 Dev Board       | 1         | Main controller                   |
| IR Sensors            | 3         | Slot detection (GPIO 18, 19, 21)  |
| Ultrasonic Sensor (HC-SR04) | 1 | Entry detection (Trig=27, Echo=26) |
| Servo Motor (SG90/MG90S) | 1 | Gate control (GPIO 16)             |
| I2C LCD 16x2 (PCF8574) | 1 | Display (SDA=21, SCL=22)           |
| Power Supply (5V)     | 1         | Common for all components         |

---

## 🧩 Pin Configuration (Default)

| Function           | GPIO Pin |
|--------------------|----------|
| IR Slot 1          | 18       |
| IR Slot 2          | 19       |
| IR Slot 3          | 21       |
| Ultrasonic Trig    | 27       |
| Ultrasonic Echo    | 26       |
| Servo Motor        | 16       |
| I2C SDA (LCD)      | 21       |
| I2C SCL (LCD)      | 22       |

> You can modify pin assignments at the top of `main.py`.

---

## 🌐 Web Dashboard

- Accessible at `http://<ESP_IP>/` (STA mode) or `http://192.168.4.1/` (AP mode)
- Displays:
  - Total, Free, and Occupied slots  
  - Real-time slot details (ID, elapsed time)
  - Recent departures with duration and fees  

### Dashboard Example
- Modern glass UI with gradient background  
- Auto-refresh every `{DASHBOARD_REFRESH}` seconds  
- Responsive design (works on mobile and desktop)

---

## 💬 Telegram Integration

1. **Create a Bot**
   - Talk to [@BotFather](https://t.me/BotFather)
   - Create a new bot → get your token (e.g. `123456789:ABCdefGHI...`)
2. **Get your Chat ID**
   - Send any message to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Copy your numeric `chat_id`
3. **Update in `main.py`**
   ```python
   TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
   TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"
## YOUTUBE DEMO

[HERE IS LIVE DEMO](https://youtube.com/shorts/Fc_cvOBn1Po?feature=share)

