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
import threading
import time

import rtlsdr

from constants import SAMPLE_RATE, SAMPLE_TIME
from detect import Detect
import events
from scan import Scan


class Receive(threading.Thread):
    def __init__(self, settings, queue):
        threading.Thread.__init__(self)
        self.name = 'Receive'

        self._settings = settings
        self._queue = queue

        self._cancel = False
        self._receive = False

        self.start()

    def __capture(self):
        sdr = rtlsdr.RtlSdr(device_index=self._settings.recvIndex)
        sdr.set_sample_rate(SAMPLE_RATE)
        if self._settings.recvGain is not None:
            sdr.set_gain(self._settings.recvGain)
        sdr.set_center_freq(self._settings.freq * 1e6)

        capture = sdr.read_samples(SAMPLE_RATE * SAMPLE_TIME)
        sdr.close()

        return capture

    def __receive(self):
        self._receive = False

        timeStamp = time.time()
        samples = self.__capture()

        scan = Scan(SAMPLE_RATE, samples)
        frequencies = scan.search()

        detect = Detect(SAMPLE_RATE, samples, frequencies)
        collars = detect.search()

        events.Post(self._queue).scan_done(collars=collars, time=timeStamp)

    def run(self):
        while not self._cancel:
            if self._receive:
                self.__receive()
            else:
                time.sleep(0.05)

    def receive(self):
        self._receive = True

    def stop(self):
        self._cancel = True
