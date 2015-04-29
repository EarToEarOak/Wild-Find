#
# Project Peregrine
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

import io
import threading

import serial
from serial.serialutil import SerialException

import events

TIMEOUT = 2


class Gps(threading.Thread):
    def __init__(self, gps, queue):
        threading.Thread.__init__(self)
        self.name = 'Location'

        self._gps = gps
        self._queue = queue

        self._comm = None
        self._commIo = None
        self._cancel = False

        self._sats = {}

        self.start()

    def __serial_read(self):
        data = True
        while data and not self._cancel:
            data = self._commIo.readline()
            yield data

        return

    def __checksum(self, data):
        checksum = 0
        for char in data:
            checksum ^= ord(char)
        return "{0:02X}".format(checksum)

    def __global_fix(self, data):
        if data[6] in ['1', '2']:
            lat = self.__coord(data[2], data[3])
            lon = self.__coord(data[4], data[5])

            events.Post(self._queue).gps_location((lon, lat))

    def __sats(self, data):
        message = int(data[1])
        messages = int(data[1])
        viewed = int(data[3])

        if message == 1:
            self._sats.clear()

        blocks = (len(data) - 4) / 4
        for i in range(0, blocks):
            sat = int(data[4 + i * 4])
            level = data[7 + i * 4]
            used = True
            if level == '':
                level = None
                used = False
            else:
                level = int(level)
            self._sats[sat] = {'Level': level,
                               'Used': used}

        if message == messages and len(self._sats) == viewed:
            events.Post(self._queue).gps_satellites(self._sats)

    def __coord(self, coord, orient):
        pos = None

        if '.' in coord:
            if coord.index('.') == 4:
                try:
                    degrees = int(coord[:2])
                    minutes = float(coord[2:])
                    pos = degrees + minutes / 60.
                    if orient == 'S':
                        pos = -pos
                except ValueError:
                    pass
            elif coord.index('.') == 5:
                try:
                    degrees = int(coord[:3])
                    minutes = float(coord[3:])
                    pos = degrees + minutes / 60.
                    if orient == 'W':
                        pos = -pos
                except ValueError:
                    pass

        return pos

    def __open(self):
        try:
            self._comm = serial.Serial(self._gps.port,
                                       baudrate=self._gps.baud,
                                       bytesize=self._gps.bits,
                                       parity=self._gps.parity,
                                       stopbits=self._gps.stops,
                                       xonxoff=self._gps.soft,
                                       timeout=TIMEOUT)
            buff = io.BufferedReader(self._comm, 1)
            self._commIo = io.TextIOWrapper(buff,
                                            newline='\r',
                                            line_buffering=True)
        except SerialException as error:
            events.Post(self._queue).gps_error(error.message)
            return False
        except OSError as error:
            events.Post(self._queue).gps_error(error)
            return False
        except ValueError as error:
            events.Post(self._queue).gps_error(error)
            return False

        return True

    def __read(self):
        for resp in self.__serial_read():
            if not len(resp):
                events.Post(self._queue).gps_error('GPS timed out')
                break
            resp = resp.replace('\n', '')
            resp = resp.replace('\r', '')
            resp = resp[1::]
            resp = resp.split('*')
            if len(resp) == 2:
                checksum = self.__checksum(resp[0])
                if checksum == resp[1]:
                    data = resp[0].split(',')
                    if data[0] == 'GPGGA':
                        self.__global_fix(data)
                    elif data[0] == 'GPGSV':
                        self.__sats(data)
                else:
                    warn = 'Invalid checksum {}, should be {}'.format(resp[1],
                                                                      checksum)
                    events.Post(self._queue).warning(warn)

    def __close(self):
        self._comm.close()

    def run(self):
        if not self.__open():
            return
        self.__read()
        self.__close()

    def stop(self):
        self._cancel = True


if __name__ == '__main__':
    print 'Please run peregrine.py'
    exit(1)
