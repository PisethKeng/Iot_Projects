from machine import Pin, time_pulse_us
from time import sleep, sleep_us

TRIG = Pin(27, Pin.OUT)
ECHO = Pin(26, Pin.IN)  

def distance_cm():
    TRIG.off(); sleep_us(2)
    TRIG.on();  sleep_us(10)
    TRIG.off()
    t = time_pulse_us(ECHO, 1, 30000)  # timeout 30ms
    if t < 0:
        return None
    return (t * 0.0343) / 2.0

while True:
    d = distance_cm()
    print("No echo" if d is None else f"{d:.1f} cm")
    sleep(0.2)
