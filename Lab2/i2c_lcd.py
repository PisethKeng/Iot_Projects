# i2c_lcd.py

from lcd_api import LcdApi
from machine import I2C
import time

# Commands
LCD_CLR = 0x01
LCD_HOME = 0x02
LCD_ENTRY_MODE = 0x04
LCD_DISPLAY_CTRL = 0x08
LCD_CURSOR_SHIFT = 0x10
LCD_FUNCTION_SET = 0x20
LCD_SET_CGRAM = 0x40
LCD_SET_DDRAM = 0x80

# Flags
ENTRY_LEFT = 0x02
DISPLAY_ON = 0x04
CURSOR_ON = 0x02
BLINK_ON = 0x01
FUNC_2LINE = 0x08
FUNC_5x8DOTS = 0x00
FUNC_4BIT = 0x00

# Control bits
ENABLE = 0x04
BACKLIGHT = 0x08

class I2cLcd(LcdApi):
    def __init__(self, i2c, i2c_addr, num_lines, num_columns):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.num_lines = num_lines
        self.num_columns = num_columns
        self.backlight = BACKLIGHT
        self.init_lcd()
        super().__init__(num_lines, num_columns)

    def hal_write_init_nibble(self, nibble):
        self.i2c.writeto(self.i2c_addr, bytearray([nibble | self.backlight | ENABLE]))
        time.sleep_ms(1)
        self.i2c.writeto(self.i2c_addr, bytearray([nibble | self.backlight]))
        time.sleep_ms(1)

    def hal_write_byte(self, data, mode=0):
        high = data & 0xF0
        low = (data << 4) & 0xF0
        self.hal_write(high | mode)
        self.hal_write(low | mode)

    def hal_write(self, data):
        self.i2c.writeto(self.i2c_addr, bytearray([data | self.backlight | ENABLE]))
        time.sleep_us(500)
        self.i2c.writeto(self.i2c_addr, bytearray([data | self.backlight]))
        time.sleep_us(500)

    def write_cmd(self, cmd):
        self.hal_write_byte(cmd, 0)

    def write_data(self, data):
        self.hal_write_byte(data, 1)

    def init_lcd(self):
        time.sleep_ms(20)
        self.hal_write_init_nibble(0x30)
        time.sleep_ms(5)
        self.hal_write_init_nibble(0x30)
        time.sleep_us(200)
        self.hal_write_init_nibble(0x30)
        time.sleep_us(200)
        self.hal_write_init_nibble(0x20)  # Set to 4-bit mode

        self.write_cmd(LCD_FUNCTION_SET | FUNC_2LINE | FUNC_5x8DOTS | FUNC_4BIT)
        self.write_cmd(LCD_DISPLAY_CTRL | DISPLAY_ON)
        self.write_cmd(LCD_CLR)
        time.sleep_ms(2)
        self.write_cmd(LCD_ENTRY_MODE | ENTRY_LEFT)

