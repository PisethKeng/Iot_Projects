## ESP32 DHT11 Relay Threshold Bot

Control Relay from telegram chat while monitoring temperature from DHT11 sensor on a ESP32.

## Project Criteria 

1. Read temperature → send to Telegram.

2. Send only when it is above 30 °C.

3. Enable remote control: Users can send /on and /off from Telegram.

4. Threshold logic: When the temperature is above 30 °C and /on is sent, the relay activates. When the temperature drops below 30 °C, the relay automatically switches OFF.

5. Group bot support: Works inside Telegram group chats instead of just direct bot chats.

## Additional Commands 
Since this project relies on temperature sensoring and my room temperature is current I added a threshhold command to modify temperature run time

_ /setth <temp_value> 

## Features 

_ Real‑time temperature and humidity monitoring with DHT11/DHT22.


<img width="941" height="540" alt="Screenshot 2025-08-30 at 10 06 06 AM" src="https://github.com/user-attachments/assets/d874e474-e3dd-432f-95be-a3fd8d4c4e36" />


_ Telegram bot interface for remote relay control.


<img width="1013" height="906" alt="Screenshot 2025-08-28 at 9 17 35 AM" src="https://github.com/user-attachments/assets/08356ee5-26a5-45cf-81f1-e82bc8507550" />



_ Auto‑alerts when temperature crosses the configured threshold.

_ Automatic relay OFF when temperature normalizes.

_ Supports group chats with Telegram bots.

<img width="843" height="926" alt="Screenshot 2025-08-28 at 9 33 58 AM" src="https://github.com/user-attachments/assets/0155346f-03ec-4463-88be-cbea1778381d" />



## Tech Stack

+ Hardware: ESP32, DHT11/DHT22 sensor, Relay module

+ Software: MicroPython, Telegram Bot API, urequests

## Learning Outcome 

_Applied IoT development using ESP32 with sensors and actuators.

_Implemented Telegram bot integration for hardware control.

_Practiced event‑driven programming with real‑world thresholds.

_Explored automation and remote monitoring for smart systems.

## --> LINK TO YOUTUBE VIDEO <--

Link to the Video: [Demo Video](https://youtu.be/g3u4ax_KVVQ)


