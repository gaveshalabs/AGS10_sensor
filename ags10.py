# MIT License
# 
# Copyright (c) 2023 Gavesha Labs
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time

""" AGS10 module """
class AGS10:
    AGS10_I2CADDR_DEFAULT = 0x1A  # Default I2C address

    def __init__(self, i2c, address=AGS10_I2CADDR_DEFAULT):
        self._i2c = i2c
        self._address = address
        self._dbuf = bytearray(5)
        self._rbuf = bytearray(5)
        self._dbuf_read_time = 0
        self._rbuf_read_time = 0
        self._init_time = time.time()
        self._validate=False

    @property
    def status(self):
        # The status byte read from the sensor, see datasheet for details
        self._read_to_dbuf()
        return self._dbuf[0]

    @property
    def is_ready(self):
        return not (self.status & 0x01)

    @property
    def total_volatile_organic_compounds_ppb(self):
        self._read_to_dbuf()
        if self._validate and self._calc_crc8(self._dbuf[0:4]) != self._dbuf[4]:
            raise AssertionError('crc mistmatched')
        return int.from_bytes(self._dbuf[1:4], 'big')

    @property
    def resistance_kohm(self):
        self._read_to_rbuf()
        if self._validate and self._calc_crc8(self._rbuf[0:4]) != self._rbuf[4]:
            raise AssertionError('crc mistmatched')
        return int.from_bytes(self._rbuf[0:4], 'big') * 0.1

    @property
    def version(self):
        buf = bytearray(5)
        self._i2c.readfrom_mem_into(self._address, 0x11, buf)
        return buf[3]

    @property
    def check_crc(self):
        return self._validate

    @check_crc.setter
    def check_crc(self, value):
        self._validate = value

    def zero_point_calibrate(self, kohm):
        data_bytes = int.to_bytes(int(kohm / 0.1), 2, 'big')
        buf = [0, 0x0C, data_bytes[0], data_bytes[1]]
        crc = self._calc_crc8(buf)
        buf = [0, 0x0C, data_bytes[0], data_bytes[1], crc]
        self._i2c.writeto_mem(self._address, 0x01, bytearray(buf))

    def zero_point_factory_reset(self):
        buf = [0, 0x0C, 0xFF, 0xFF, 0x81]
        self._i2c.writeto_mem(self._address, 0x01, bytearray(buf))

    def update_address(self, new_addr):
        new_addr_inv = ~new_addr
        buf = [new_addr, new_addr_inv, new_addr, new_addr_inv]
        crc = self._calc_crc8(buf)
        buf = [new_addr, new_addr_inv, new_addr, new_addr_inv, crc]
        self._i2c.writeto_mem(self._address, 0x21, bytearray(buf))


    """ Private functions """
    def _read_to_dbuf(self):
        if time.time() - self._dbuf_read_time < 2:
            # min 1.5s delay is required between successive data acquisitions
            return
        # Read sensor data to buffer
        self._i2c.readfrom_into(self._address, self._dbuf, True)
        self._dbuf_read_time = time.time()

    def _read_to_rbuf(self):
        if time.time() - self._rbuf_read_time < 2:
            # min 1.5s delay is required between successive resistance reads
            return
        # Read sensor data to buffer
        self._i2c.readfrom_mem_into(self._address, 0x20, self._rbuf)
        self._rbuf_read_time = time.time()

    def _calc_crc8(self, data):
        crc=0xFF
        for byte in data :
            crc^=byte
            for i in range(8) :
                crc=((crc<<1)^0x31) if crc & 0x80 else crc<<1
        return crc&0xFF