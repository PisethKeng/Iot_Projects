# LAB2 – IoT Webserver with LED, Sensors, and LCD Control

ESP32-based IoT webserver built with **MicroPython**.  
This project provides a browser-based dashboard to control an LED, read sensors, and display data or custom text on an LCD.

---

## Features

- Web-based LED ON/OFF control  
- Live temperature (DHT11) and distance (HC-SR04) readings  
- Automatic sensor refresh (every 1–2 seconds)  
- Display temperature and distance on a 16×2 I²C LCD  
- Send custom text from web page to LCD  
- Responsive web UI hosted directly on ESP32  

---

## Hardware Used

- ESP32 Dev Board (MicroPython)
- DHT11 temperature sensor
- HC-SR04 ultrasonic distance sensor
- 16×2 LCD with I²C backpack
- USB cable
- Wi-Fi network

---

## Software Setup

### 1. Flash MicroPython

Download and flash the ESP32 MicroPython firmware:

https://micropython.org/download/esp32/

---

### 2. Upload Files to ESP32

Upload the following files using **Thonny**:

main_dashboard.py
lcd_api.py
i2c_lcd.py
machine_i2c_lcd.py
ultrasonic.py

## LAB2-IoT-Webserver/

├── main_dashboard.py
├── machine_i2c_lcd.py
├── lcd_api.py
├── i2c_lcd.py
├── ultrasonic.py
├── README.md
├── screenshots/
│   ├── wiring.png
│   ├── web_ui.png
│   └── lcd_output.png
└── demo_video.mp4
