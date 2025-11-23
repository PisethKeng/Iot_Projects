## ESP32 Motor Control & InfluxDB Telemetry Project

This project implements an ESP32-based motor control system with real-time telemetry logging to an InfluxDB database. It includes:

Wi-Fi connection to local network

Motor PWM control

HTTP POST requests to InfluxDB

A lightweight onboard web server (optional)

Logging of motor direction, speed, timestamps, and system state

This repository also includes screenshots and documentation evidence for all required tasks.

🧩 Project Overview

The ESP32 is programmed using MicroPython and controls a DC motor using PWM.
Telemetry (RPM approximation, control commands, run logs) is sent to InfluxDB via HTTP.

An external dashboard such as Grafana can query the same InfluxDB database to visualize real-time motor data.

# 🚀 Features

✔️ ESP32 Wi-Fi auto-connection

✔️ Secure credentials stored in constants

✔️ Motor PWM speed control

✔️ Forward / Backward direction control

✔️ Pushes data to InfluxDB using the /write API

✔️ Lightweight web server for interactive browser-based control

✔️ Timestamps for accurate measurement

✔️ Debug logging

# 📁 Repository Structure
📂 esp32-motor-influxdb
├── main.py              # Motor control + Wi-Fi + InfluxDB logging
├── README.md            # Project documentation
├── /evidence/           # Screenshots for each required task (insert later)
│   ├── wifi_connection.png
│   ├── influxdb_write.png
│   ├── grafana_dashboard.png
│   └── motor_running.png
└── requirements.txt     # (If needed)

# 🔧 Hardware Requirements

ESP32 Dev Module

L298N or compatible motor driver

DC motor

External power supply (recommended)

Jumper wires

Optional: Breadboard

# 🧪 Software Requirements

MicroPython (ESP32 firmware)

ampy or mpremote for file uploads

InfluxDB (local or cloud)

Grafana (optional, for visualization)

# 📡 Wi-Fi Configuration

Modify the following lines in main.py when switching networks:

WIFI_SSID = "YourWiFiName"
WIFI_PASS = "YourPassword"

# 📊 InfluxDB Setup

Install InfluxDB

Create a database:

CREATE DATABASE motor_logs


Replace the default URL in main.py:

INFLUX_URL = "http://<your-ip>:8086/write?db=motor_logs&precision=s"


Example (home network):

http://10.30.0.157:8086/write?db=motor_logs&precision=s

