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

import ctypes
import threading
import time

import rtlsdr

from harrier import events
from harrier.constants import SAMPLE_RATE, SAMPLE_TIME, BLOCKS
from harrier.detect import Detect, stream_to_complex
from harrier.scan import Scan


class Receive(threading.Thread):
    def __init__(self, settings, queue):
        threading.Thread.__init__(self)
        self.name = 'Receive'
        self.daemon = True

        self._settings = settings
        self._queue = queue

        self._cancel = False
        self._receive = False

        self._sdr = None
        self._capture = (ctypes.c_ubyte * int(2 * SAMPLE_RATE * SAMPLE_TIME))()

        self._captureBlock = 0
        self._timeStamp = None

        devices = rtlsdr.librtlsdr.rtlsdr_get_device_count()
        if self._settings.recvIndex >= devices:
            error = 'Cannot find device at index {}'
            error = error.format(self._settings.recvIndex)
            events.Post(self._queue).error(error=error)
        else:
            self.start()

    def __capture(self, data, _sdr):
        length = len(data)
        pos = self._captureBlock * length
        dst = ctypes.byref(self._capture, pos)
        ctypes.memmove(dst, data, length * ctypes.sizeof(ctypes.c_ubyte))

        self._captureBlock += 1
        if self._captureBlock == BLOCKS:
            self._sdr.cancel_read_async()
            self._captureBlock = 0

    def __receive(self):
        self._receive = False

        events.Post(self._queue).status(events.STATUS_CAPTURE)

        try:
            if self._sdr is None:
                self._sdr = rtlsdr.RtlSdr(device_index=self._settings.recvIndex)
                self._sdr.set_sample_rate(SAMPLE_RATE)
                self._sdr.set_center_freq(self._settings.freq * 1e6)
                if self._settings.recvGain is not None:
                    self._sdr.set_gain(self._settings.recvGain)
                else:
                    self._sdr.set_gain(0)
            self._timeStamp = time.time()

            self._sdr.read_bytes_async(self.__capture,
                                       2 * SAMPLE_RATE * SAMPLE_TIME / BLOCKS)

            events.Post(self._queue).status(events.STATUS_PROCESS)
            iq = stream_to_complex(self._capture)
            scan = Scan(SAMPLE_RATE, iq)
            frequencies = scan.search(self._settings.scanFast)

            detect = Detect(SAMPLE_RATE, iq, frequencies)
            collars = detect.search()

            events.Post(self._queue).status(events.STATUS_IDLE)
            events.Post(self._queue).scan_done(collars=collars,
                                               timeStamp=self._timeStamp)

        except IOError as e:
            error = 'Capture failed: {}'.format(e.message)
            events.Post(self._queue).error(error=error)

    def run(self):
        while not self._cancel:
            if self._receive:
                self.__receive()
            else:
                try:
                    time.sleep(0.1)
                except IOError:
                    pass

    def receive(self):
        self._receive = True

    def stop(self):
        self._cancel = True
        if self._sdr is not None:
            try:
                self._sdr.cancel_read_async()
            except IOError:
                pass


if __name__ == '__main__':
    print 'Please run harrier.py'
    exit(1)
