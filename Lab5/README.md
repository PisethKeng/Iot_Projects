<img width="1728" height="1117" alt="Screenshot 2025-11-20 at 7 27 51 PM" src="https://github.com/user-attachments/assets/bca5a88c-89e8-42e0-88ba-a9def3caf831" /># 🚀 Mobile App DC Motor Control with Grafana Dashboard



This repository contains my completed implementation of Lab 5: Mobile App DC Motor Control with Grafana Dashboard.
I successfully built a full IoT actuation system where a mobile app controls a DC motor through an ESP32 web server, with all actions logged into InfluxDB and visualized in Grafana.


## 📌 Project Overview

I developed an ESP32-based MicroPython web server that exposes REST endpoints:

/forward
/backward
/stop
/speed?value=<0–100>


A custom mobile app built using MIT App Inventor sends these HTTP commands over Wi-Fi.
Every command (direction + speed) is recorded into InfluxDB and displayed live in Grafana.


## 🎯 Learning Outcomes Achieved

I completed all required learning outcomes:

Designed an IoT actuation system combining ESP32, L298N, mobile UI, and Grafana.

Created a RESTful interface for motor control using MicroPython.

Built and deployed a mobile control UI using MIT App Inventor.

Logged all actuator data into InfluxDB and visualized it on Grafana.

Evaluated delay, responsiveness, and system reliability.


## 🛠️ Hardware Setup

ESP32 Dev Board

L298N Motor Driver

DC Motor

Jumper wires + breadboard

Android phone (App Inventor app)

InfluxDB server

Grafana Dashboard


## 🔌 Wiring Diagram
ESP32 Pin	L298N Pin	Purpose
25	ENA	PWM (Speed)
26	IN1	Direction
27	IN2	Direction
GND	GND	Common Ground
		

## 📱 Mobile App (MIT App Inventor)

The mobile app UI includes:

Forward, Backward, Stop buttons

Speed slider (0–100%)

Status label showing current command

It sends commands such as:

http://<ESP_IP>/forward?speed=80
http://<ESP_IP>/backward?speed=50
http://<ESP_IP>/stop
http://<ESP_IP>/speed?value=60


<img width="869" height="528" alt="Screenshot 2025-11-22 at 2 11 15 PM" src="https://github.com/user-attachments/assets/2bf666d6-1810-423a-8582-1fc35d5cf809" />


## 🧠 ESP32 MicroPython (Web Server + InfluxDB Logging)

I implemented all required endpoints and added HTTP POST logging to InfluxDB.
Each motor command sends a JSON log:

{
  "timestamp": "<ISO_time>",
  "action": "forward",
  "speed": 70
}


## 🖥️ serial log screenshot here


<img width="1728" height="1117" alt="Screenshot 2025-11-22 at 2 08 32 PM" src="https://github.com/user-attachments/assets/a6dcb330-dd73-4cd3-8cbc-c9a70927b70e" />


## 🗄️ InfluxDB Data Logging

InfluxDB successfully stores:

action

speed value

timestamp

## 🗄️  screenshot of InfluxDB table here

<img width="869" height="528" alt="Screenshot 2025-11-22 at 2 10 32 PM" src="https://github.com/user-attachments/assets/43581327-84e0-4ca0-a123-e5b91b197293" />



## 📊 Grafana Dashboard

My Grafana dashboard includes:

Speed vs Time graph

Last command display

Events table with timestamp + direction + speed

## 📊  Grafana dashboard screenshot here


<img width="1728" height="1117" alt="Screenshot 2025-11-21 at 6 37 59 PM" src="https://github.com/user-attachments/assets/a3d75edd-f161-4335-b31a-96e6003a13a6" />

<img width="1728" height="1117" alt="Screenshot 2025-11-21 at 6 34 02 PM" src="https://github.com/user-attachments/assets/0e965622-c5ac-4bcb-9244-c0f2d2a285d0" />

<img width="1728" height="1117" alt="Screenshot 2025-11-21 at 6 27 46 PM" src="https://github.com/user-attachments/assets/cda2aee3-d7e6-42a1-b208-b5801b879b80" />

## 🛡️ Reliability Improvements Implemented

I added:

Wi-Fi auto-reconnect logic

Error handling for invalid HTTP requests

Smoother request parsing

Logging fallback behaviour during network drops



🎥 Demonstration Video

A short demo video shows:

Mobile app controlling the motor

ESP32 responding instantly

Grafana updating in real time


📝 Reflection

In my testing:

Wi-Fi latency was generally low, with occasional small delays under weak signal conditions.

InfluxDB logging was reliable; occasional spikes came from network reconnection events.

Grafana’s real-time updates accurately reflected the live state of the motor.

Overall responsiveness and accuracy were good, with potential future improvements in debouncing and data smoothing.
