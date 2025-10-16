# main_consolidated.py - ESP32 Smart Parking System with Fixed Entry/Exit Logic

import utime
import time
import math
import urequests
import network
import socket
from machine import Pin, PWM, I2C, time_pulse_us
from time import sleep_ms

# --- 1. CONFIGURATION ---
WIFI_SSID = "Robotic WIFI"
WIFI_PASS = "rbtWIFI@2025"

TELEGRAM_BOT_TOKEN = "8445543114:AAHohUU6gOinkSUURwE5KMTP2ZyScFyk0yA"
CHAT_ID = "902331687"

PIN_ULTRASONIC_TRIG = 27
PIN_ULTRASONIC_ECHO = 26
PIN_SERVO = 16
PIN_IR_S1 = 5
PIN_IR_S2 = 19
PIN_IR_S3 = 17
I2C_SCL = 22
I2C_SDA = 21
I2C_FREQ = 400000

NUM_SLOTS = 3
ENTRY_DEBOUNCE_MS = 300
EXIT_GRACE_MS = 1000
ULTRASONIC_DETECT_CM = 10
ULTRASONIC_COOLDOWN_MS = 5000  # Prevent multiple triggers (5 seconds)
FEE_PER_MIN = 0.5
WEBSERVER_PORT = 80
DASHBOARD_REFRESH = 3
GATE_OPEN_TIME_MS = 3000
SERVO_STEP = 50

PIN_LED_GATE = 21
PIN_LED_FULL = 22

# --- 2. WIFI HELPER ---
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        start = time.time()
        while not wlan.isconnected():
            if time.time() - start > 15:
                raise RuntimeError("WiFi connection failed")
            time.sleep(1)
    ip = wlan.ifconfig()[0]
    print("Connected, IP:", ip)
    return ip

# --- 3. TELEGRAM API ---
TELEGRAM_API_URL = "https://api.telegram.org/bot{}/sendMessage"

def format_ms_to_datetime(ms_since_boot):
    now_sec = utime.time()
    elapsed_ms = utime.ticks_ms()
    time_event_sec = now_sec - (elapsed_ms - ms_since_boot) // 1000
    t = utime.localtime(time_event_sec)
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*t[:6])

def send_message(text):
    try:
        url = TELEGRAM_API_URL.format(TELEGRAM_BOT_TOKEN)
        data = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
        r = urequests.post(url, json=data, timeout=5)
        r.close()
        return r.status_code == 200
    except:
        return False

def send_receipt_from_ticket(ticket):
    message = (
        f"✅ *Ticket CLOSED (ID: {ticket.id})*\n"
        f"Slot: `{ticket.slot}`\n"
        f"Entry: `{format_ms_to_datetime(ticket.time_in_ms)}`\n"
        f"Exit: `{format_ms_to_datetime(ticket.time_out_ms)}`\n"
        f"Duration: *{ticket.duration_min} minutes*\n"
        f"Fee Charged: *${ticket.fee:.2f}*"
    )
    send_message(message)

# --- 4. LCD API ---
class LcdApi:
    def __init__(self):
        self.num_lines = 2
        self.num_columns = 16
    def putchar(self, char): raise NotImplementedError
    def clear(self): raise NotImplementedError
    def move_to(self, col, row): raise NotImplementedError
    def putstr(self, string):
        for ch in string: self.putchar(ch)

MASK_RS = 0x01
MASK_RW = 0x02
MASK_E  = 0x04
SHIFT_BACKLIGHT = 3
BACKLIGHT = 1 << SHIFT_BACKLIGHT

class I2cLcd(LcdApi):
    def __init__(self, i2c, addr, rows, cols):
        super().__init__()
        self.i2c = i2c
        self.addr = addr
        self.num_lines = rows
        self.num_columns = cols
        self.backlight = BACKLIGHT
        self._init_lcd()

    def _write_byte(self, data):
        self.i2c.writeto(self.addr, bytes([data | self.backlight]))
    def _pulse(self, data):
        self._write_byte(data | MASK_E)
        sleep_ms(1)
        self._write_byte(data & ~MASK_E)
        sleep_ms(1)
    def _write_nibble(self, nibble):
        self._write_byte(nibble)
        self._pulse(nibble)
    def _cmd(self, cmd):
        hi = cmd & 0xF0
        lo = (cmd << 4) & 0xF0
        self._write_nibble(hi)
        self._write_nibble(lo)
    def _init_lcd(self):
        sleep_ms(50)
        self._write_byte(0x30); self._pulse(0x30); sleep_ms(5)
        self._pulse(0x30); sleep_ms(1); self._pulse(0x20); sleep_ms(1)
        self._cmd(0x28); self._cmd(0x0C); self._cmd(0x01); sleep_ms(2); self._cmd(0x06)
    def clear(self):
        self._cmd(0x01); sleep_ms(2)
    def move_to(self, col, row):
        row_offsets = [0x00,0x40,0x14,0x54]
        self._cmd(0x80 | (col + row_offsets[row]))
    def putchar(self, char):
        val = ord(char)
        hi = val & 0xF0
        lo = (val <<4)&0xF0
        self._write_nibble(hi|MASK_RS)
        self._write_nibble(lo|MASK_RS)

# --- 5. PARKING LOGIC ---
class Slot:
    def __init__(self,name):
        self.name = name
        self.occupied = False
        self.assigned_id = None
        self.time_in_ms = None
        self.ir_state_ms = utime.ticks_ms()

class Ticket:
    def __init__(self,id_,slot_name,time_in_ms):
        self.id = id_
        self.slot = slot_name
        self.time_in_ms = time_in_ms
        self.time_out_ms = None
        self.duration_min = None
        self.fee = None
    def close(self,time_out_ms):
        self.time_out_ms = time_out_ms
        duration_min = max(math.ceil(utime.ticks_diff(self.time_out_ms,self.time_in_ms)/60000),0)
        self.duration_min = duration_min
        self.fee = duration_min*FEE_PER_MIN

class ParkingManager:
    def __init__(self):
        self.slots = [Slot(f"S{i+1}") for i in range(NUM_SLOTS)]
        self.open_tickets = {}
        self.closed_tickets = []
        self.next_ids = list(range(1,NUM_SLOTS+1))
        self.recently_occupied = {}
        self.pending_entry = False  # Flag for car waiting to enter

    def assign_lowest_id(self):
        return min(self.next_ids) if self.next_ids else None

    def has_available_slot(self):
        """Check if there's at least one free slot"""
        return any(not s.occupied for s in self.slots)

    def mark_occupied(self, idx):
        s = self.slots[idx]
        if s.occupied: return None
        assigned = self.assign_lowest_id()
        if assigned is None: return None
        self.next_ids.remove(assigned)
        s.assigned_id = assigned; s.occupied=True; s.time_in_ms=utime.ticks_ms()
        t = Ticket(assigned, s.name, s.time_in_ms)
        self.open_tickets[assigned] = t
        self.recently_occupied[s.name] = utime.ticks_ms()
        print("Assigned ID", assigned, "to", s.name)
        return assigned

    def mark_free(self, idx):
        s = self.slots[idx]
        if not s.occupied: return None
        assigned = s.assigned_id
        t = self.open_tickets.pop(assigned, None)
        if t:
            t.close(utime.ticks_ms())
            self.closed_tickets.insert(0, t)
            send_receipt_from_ticket(t)
        s.occupied=False; s.assigned_id=None; s.time_in_ms=None
        if assigned not in self.next_ids:
            self.next_ids.append(assigned); self.next_ids.sort()
        print("Ticket closed ID", assigned, "slot", s.name)
        return t

    def process_ir_states(self, ir_states):
        """
        Monitor IR sensors for vehicles in slots.
        Returns (changed, exit_detected)
        - changed: True if slot status changed
        - exit_detected: True if car left slot (should open gate for exit)
        """
        changed = False
        exit_detected = False
        now = utime.ticks_ms()
        
        for i, raw_state in enumerate(ir_states):
            s = self.slots[i]
            was_occupied = s.occupied
            is_blocked = s.ir_state_ms > 0
            elapsed = utime.ticks_diff(now, abs(s.ir_state_ms))
            
            # Update state timestamp when IR state changes
            if raw_state != is_blocked:
                s.ir_state_ms = now if raw_state else -now
            
            # ENTRY: IR blocked on empty slot (car parking)
            if raw_state and not s.occupied and elapsed >= ENTRY_DEBOUNCE_MS:
                self.mark_occupied(i)
                changed = True
                s.ir_state_ms = now
                print(f"Car parked in {s.name}")
            
            # EXIT: IR unblocked on occupied slot (car leaving)
            elif not raw_state and s.occupied and elapsed >= EXIT_GRACE_MS:
                self.mark_free(i)
                changed = True
                exit_detected = True  # Trigger gate opening
                s.ir_state_ms = -now
                print(f"Car leaving {s.name}")

        # Cleanup recently_occupied older than 60s
        to_remove = []
        for slot_name, ts in self.recently_occupied.items():
            if utime.ticks_diff(now, ts) > 60000:
                to_remove.append(slot_name)
        for slot_name in to_remove:
            del self.recently_occupied[slot_name]
        
        return changed, exit_detected

    def get_status(self):
        total=len(self.slots)
        free=sum(1 for s in self.slots if not s.occupied)
        occupied=total-free
        slots_info=[]
        now=utime.ticks_ms()
        for s in self.slots:
            elapsed_min=None
            if s.occupied and s.time_in_ms:
                elapsed_min=utime.ticks_diff(now,s.time_in_ms)/60000.0
            slots_info.append({"name":s.name,"occupied":s.occupied,"id":s.assigned_id,"elapsed_min":elapsed_min})
        return {
            "total":total,
            "free":free,
            "occupied":occupied,
            "slots":slots_info,
            "open_tickets":list(self.open_tickets.values()),
            "recent_closed":self.closed_tickets[:10],
            "recently_occupied": self.recently_occupied
        }

# --- 6. WEBSERVER ---
def render_dashboard_html(status):
    slots_html=""
    for s in status["slots"]:
        elapsed="-"
        if s["occupied"] and s["elapsed_min"]: elapsed="{:.1f} min".format(s["elapsed_min"])
        if s["occupied"]:
            if s["name"] in status.get('recently_occupied', {}):
                row_class="flash"
            else:
                row_class="occupied"
        else:
            row_class="free"
        slots_html+=f"<tr class='{row_class}'><td>{s['name']}</td><td>{'Occupied' if s['occupied'] else 'Free'}</td><td>{s['id'] or '-'}</td><td>{elapsed}</td></tr>"

    departures_html=""
    for t in status["recent_closed"]:
        departures_html += f"<tr style='background:#eeeeff'><td>{t.id}</td><td>{t.slot}</td><td>{format_ms_to_datetime(t.time_out_ms)}</td><td>{t.fee:.2f}</td></tr>"

    html=f"""
<html>
<head>
<title>Smart Parking — Dashboard</title>
<meta http-equiv="refresh" content="{DASHBOARD_REFRESH}">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root {{
  --bg: linear-gradient(160deg, #0a1f44 0%, #1a2b5a 100%);
  --card-bg: rgba(255,255,255,0.08);
  --border: rgba(255,255,255,0.15);
  --text: #e9ecf8;
  --accent1: #5b8cff;
  --accent2: #19c37d;
  --warn: #ff6b6b;
}}
body {{
  margin: 0;
  padding: 20px;
  font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: var(--text);
  background: var(--bg);
  background-attachment: fixed;
}}
h2 {{
  text-align: center;
  font-size: 26px;
  margin-top: 10px;
  background: linear-gradient(90deg,var(--accent1),var(--accent2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}}
.card {{
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px;
  margin: 20px auto;
  box-shadow: 0 8px 20px rgba(0,0,0,0.2);
  max-width: 900px;
}}
.card h3 {{
  border-bottom: 1px solid var(--border);
  padding-bottom: 6px;
  margin-top: 0;
  color: var(--accent1);
}}
table {{
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
  border-radius: 10px;
  overflow: hidden;
}}
th {{
  background: var(--accent1);
  color: #fff;
  padding: 10px;
  text-align: left;
  font-weight: 600;
  letter-spacing: .5px;
}}
td {{
  padding: 10px;
  border-bottom: 1px solid var(--border);
}}
tr.free {{ background: rgba(25,195,125,0.1); }}
tr.occupied {{ background: rgba(255,107,107,0.1); }}
tr.flash {{ animation: pulseRow 1s ease-in-out infinite; }}
@keyframes pulseRow {{
  0% {{ background: rgba(255,107,107,0.1); }}
  50% {{ background: rgba(255,107,107,0.3); }}
  100% {{ background: rgba(255,107,107,0.1); }}
}}
.summary {{
  display: flex;
  justify-content: space-evenly;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 16px;
  text-align: center;
}}
.badge {{
  padding: 8px 14px;
  border-radius: 999px;
  background: var(--accent1);
  color: white;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
}}
.badge.free {{ background: var(--accent2); }}
.badge.occ {{ background: var(--warn); }}
footer {{
  text-align: center;
  margin-top: 20px;
  font-size: 13px;
  color: var(--text);
  opacity: .7;
}}
</style>
</head>
<body>
<h2>🚗 Smart Parking Dashboard</h2>

<div class="card">
  <div class="summary">
    <div class="badge">Total: {status['total']}</div>
    <div class="badge free">Free: {status['free']}</div>
    <div class="badge occ">Occupied: {status['occupied']}</div>
  </div>
</div>

<div class="card">
  <h3>Current Slot Status</h3>
  <table>
    <tr><th>Slot</th><th>Status</th><th>ID</th><th>Elapsed</th></tr>
    {slots_html}
  </table>
</div>

<div class="card">
  <h3>Recent Departures</h3>
  <table>
    <tr><th>Ticket ID</th><th>Slot</th><th>Exit Time</th><th>Fee ($)</th></tr>
    {departures_html}
  </table>
</div>

<footer>
  Auto-refresh every {DASHBOARD_REFRESH}s • ESP32 Smart Parking System
</footer>
</body>
</html>

"""
    return html

class WebServer:
    def __init__(self, port=WEBSERVER_PORT):
        self.addr=socket.getaddrinfo("0.0.0.0",port)[0][-1]
        self.sock=socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.sock.bind(self.addr)
        self.sock.listen(1)
        self.sock.settimeout(0.1)
        print("Web server listening on port",port)
    def poll(self,parking):
        try:
            cl,addr=self.sock.accept()
        except: return
        try:
            cl.recv(1024)
            html=render_dashboard_html(parking.get_status())
            cl.send(b"HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n")
            cl.send(html.encode())
        finally:
            cl.close()

# --- 7. HARDWARE SETUP ---
TRIG=Pin(PIN_ULTRASONIC_TRIG,Pin.OUT)
ECHO=Pin(PIN_ULTRASONIC_ECHO,Pin.IN)
SERVO_PIN=Pin(PIN_SERVO,Pin.OUT)
IR_PINS=[Pin(PIN_IR_S1,Pin.IN),Pin(PIN_IR_S2,Pin.IN),Pin(PIN_IR_S3,Pin.IN)]
LED_GATE=Pin(PIN_LED_GATE,Pin.OUT)
LED_FULL=Pin(PIN_LED_FULL,Pin.OUT)
servo=PWM(SERVO_PIN,freq=50)
servo_angle=0
target_angle=0
servo_last_update=utime.ticks_ms()
gate_close_time=0
last_ultrasonic_trigger=0
gate_is_operating=False  # Flag to prevent retriggering during gate operation

def servo_write(angle):
    min_us=500; max_us=2500
    pulse_us=min_us+(angle/180)*(max_us-min_us)
    duty=int((pulse_us/20000)*1023)
    servo.duty(duty)

def update_servo():
    global servo_angle,target_angle,servo_last_update
    now=utime.ticks_ms()
    if utime.ticks_diff(now,servo_last_update)>=20:
        if servo_angle<target_angle:
            servo_angle+=SERVO_STEP
            if servo_angle>target_angle: servo_angle=target_angle
        elif servo_angle>target_angle:
            servo_angle-=SERVO_STEP
            if servo_angle<target_angle: servo_angle=target_angle
        servo_write(servo_angle)
        servo_last_update=now

def open_gate():
    global target_angle, gate_close_time, gate_is_operating
    if not gate_is_operating:
        target_angle=90
        LED_GATE.value(1)
        gate_close_time=utime.ticks_add(utime.ticks_ms(),GATE_OPEN_TIME_MS)
        gate_is_operating = True
        print("Gate opening...")

def close_gate():
    global target_angle, gate_close_time, gate_is_operating, last_ultrasonic_trigger
    if gate_is_operating:
        target_angle=0
        LED_GATE.value(0)
        gate_close_time=0
        gate_is_operating = False
        last_ultrasonic_trigger = utime.ticks_ms()  # Start cooldown
        print("Gate closed")

def read_ultrasonic():
    TRIG.value(0)
    time.sleep_us(2)
    TRIG.value(1)
    time.sleep_us(10)
    TRIG.value(0)
    dur=time_pulse_us(ECHO,1,30000)
    return dur/58.3 if dur>=0 else 999

def update_lcd_display(parking,lcd_):
    if not lcd_: return
    status=parking.get_status()
    free=status["free"]
    lcd_.clear()
    if free==0:
        lcd_.putstr("PARKING FULL"); LED_FULL.value(1)
    else:
        lcd_.putstr(f"FREE:{free}/{status['total']}"); LED_FULL.value(0)

# --- INITIALIZATION ---
try: IP_ADDRESS=connect_wifi()
except: IP_ADDRESS=None

lcd=None
try:
    i2c=I2C(0,scl=Pin(I2C_SCL),sda=Pin(I2C_SDA),freq=I2C_FREQ)
    dev=i2c.scan()
    if not dev: raise Exception("No LCD found")
    lcd=I2cLcd(i2c,dev[0],2,16)
    lcd.clear()
    lcd.putstr(f"IP:{IP_ADDRESS or 'N/A'}")
except: print("LCD init failed")

parking=ParkingManager()
webserver=WebServer()
servo_write(0)
LED_GATE.value(0); LED_FULL.value(0)
update_lcd_display(parking,lcd)

# --- MAIN LOOP ---
print("System ready. Entry: Ultrasonic | Exit: IR sensors")

while True:
    now = utime.ticks_ms()
    update_servo()
    
    # Auto-close gate after timeout (gate opens -> waits -> closes naturally)
    if gate_close_time and utime.ticks_diff(now, gate_close_time) >= 0:
        close_gate()
    
    # ENTRY DETECTION: Ultrasonic sensor detects car approaching
    # Only trigger if: gate is not operating AND cooldown period has passed
    if not gate_is_operating and utime.ticks_diff(now, last_ultrasonic_trigger) >= ULTRASONIC_COOLDOWN_MS:
        distance = read_ultrasonic()
        if distance <= ULTRASONIC_DETECT_CM:
            if parking.has_available_slot():
                print(f"ENTRY: Car detected at {distance:.1f}cm - Opening gate")
                open_gate()  # Gate will open, then close automatically after timeout
                update_lcd_display(parking, lcd)
            else:
                print("ENTRY DENIED: Parking full")
    
    # EXIT DETECTION: IR sensors detect car leaving slot
    raw_ir = [pin.value() == 0 for pin in IR_PINS]
    changed, exit_detected = parking.process_ir_states(raw_ir)
    
    if changed:
        update_lcd_display(parking, lcd)
    
    # Open gate when car exits (only if gate is not already operating)
    if exit_detected and not gate_is_operating:
        print("EXIT: Opening gate for departing car")
        open_gate()  # Gate will open, then close automatically after timeout
    
    webserver.poll(parking)
    time.sleep(0.05)