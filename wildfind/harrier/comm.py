#!/usr/bin/env python
#
#
# Wild Find
#
#
# Copyright 2014 - 2015 Al Brown
#
# Wildlife tracking and mapping
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import serial
from serial.tools import list_ports


class Comm(object):
    BITS = [serial.FIVEBITS, serial.SIXBITS, serial.SEVENBITS,
            serial.EIGHTBITS]
    PARITIES = [serial.PARITY_NONE, serial.PARITY_EVEN, serial.PARITY_ODD,
                serial.PARITY_MARK, serial.PARITY_SPACE]
    STOPS = [serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE,
             serial.STOPBITS_TWO]

    def __init__(self):
        self.port = None
        self.baud = 115200
        self.bits = serial.EIGHTBITS
        self.parity = serial.PARITY_NONE
        self.stops = serial.STOPBITS_ONE
        self.soft = False

    def get_ports(self):
        return list_ports.comports()

    def get_bauds(self):
        return serial.Serial.BAUDRATES


if __name__ == '__main__':
    print 'Please run harrier.py'
    exit(1)
