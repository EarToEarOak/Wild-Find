#!/usr/bin/env python
#
#
# Wild Find
#
#
# Copyright 2014 - 2017 Al Brown
#
# Wildlife tracking and mapping
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation
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

from wildfind.harrier import events
from wildfind.harrier.constants import SAMPLE_RATE, SAMPLE_TIME, BLOCKS
from wildfind.harrier.detect import Detect, stream_to_complex
from wildfind.harrier.scan import Scan


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
            events.Post(self._queue).error(error)
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
                time.sleep(1)
                self._sdr.set_gain(self._settings.recvGain)
                cal = int(self._settings.recvCal)
                if cal != 0:
                    self._sdr.set_freq_correction(cal)
            self._timeStamp = time.time()

            self._sdr.read_bytes_async(self.__capture,
                                       2 * SAMPLE_RATE * SAMPLE_TIME / BLOCKS)
            if self._cancel:
                return

            events.Post(self._queue).status(events.STATUS_PROCESS)
            iq = stream_to_complex(self._capture)
            if self._cancel:
                return

            scan = Scan(SAMPLE_RATE, iq)
            frequencies = scan.search()
            if self._cancel:
                return

            detect = Detect(SAMPLE_RATE, iq, frequencies)
            collars = detect.search(self._settings.freq * 1e6)

            events.Post(self._queue).status(events.STATUS_IDLE)
            events.Post(self._queue).scan_done(collars=collars,
                                               timeStamp=self._timeStamp)

        except IOError as e:
            error = 'Capture failed: {}'.format(e.message)
            events.Post(self._queue).error(error)

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
