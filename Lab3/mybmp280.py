import struct, math, time

class BMP280:
    def __init__(self, i2c, addr=0x76):
        self.i2c = i2c
        self.addr = addr
        chip_id = self.i2c.readfrom_mem(self.addr, 0xD0, 1)[0]
        if chip_id != 0x58:
            raise RuntimeError("Not a BMP280, ID=%#x" % chip_id)
        self._load_calibration()
        # Normal mode, temp+press oversampling x1
        self.i2c.writeto_mem(self.addr, 0xF4, b'\x27')
        self.i2c.writeto_mem(self.addr, 0xF5, b'\xA0')

    def _load_calibration(self):
        buf = self.i2c.readfrom_mem(self.addr, 0x88, 24)
        (self.T1, self.T2, self.T3,
         self.P1, self.P2, self.P3, self.P4, self.P5,
         self.P6, self.P7, self.P8, self.P9) = struct.unpack("<HhhHhhhhhhhh", buf)
        self.t_fine = 0

    def _read_raw(self):
        d = self.i2c.readfrom_mem(self.addr, 0xF7, 6)
        adc_p = (d[0] << 12) | (d[1] << 4) | (d[2] >> 4)
        adc_t = (d[3] << 12) | (d[4] << 4) | (d[5] >> 4)
        return adc_t, adc_p

    def _comp_temp(self, adc_t):
        var1 = (((adc_t >> 3) - (self.T1 << 1)) * self.T2) >> 11
        var2 = (((((adc_t >> 4) - self.T1) * ((adc_t >> 4) - self.T1)) >> 12) * self.T3) >> 14
        self.t_fine = var1 + var2
        T = (self.t_fine * 5 + 128) >> 8
        return T / 100.0

    def _comp_press(self, adc_p):
        var1 = self.t_fine - 128000
        var2 = var1 * var1 * self.P6
        var2 = var2 + ((var1 * self.P5) << 17)
        var2 = var2 + (self.P4 << 35)
        var1 = ((var1 * var1 * self.P3) >> 8) + ((var1 * self.P2) << 12)
        var1 = (((1 << 47) + var1) * self.P1) >> 33
        if var1 == 0:
            return 0
        p = 1048576 - adc_p
        p = (((p << 31) - var2) * 3125) // var1
        var1 = (self.P9 * (p >> 13) * (p >> 13)) >> 25
        var2 = (self.P8 * p) >> 19
        p = ((p + var1 + var2) >> 8) + (self.P7 << 4)
        return p / 256.0

    @property
    def temperature(self):
        adc_t, _ = self._read_raw()
        return self._comp_temp(adc_t)

    @property
    def pressure(self):
        adc_t, adc_p = self._read_raw()
        self._comp_temp(adc_t)
        return self._comp_press(adc_p)

    @property
    def altitude(self):
        p = self.pressure
        return 44330 * (1 - (p / 101325) ** (1 / 5.255))
