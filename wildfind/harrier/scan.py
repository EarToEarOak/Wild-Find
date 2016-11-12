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

import numpy

from wildfind.harrier.psd import psd
from wildfind.harrier.utils import Utils


# FFT bins used to search
SCAN_BINS = 4096
# Peak level change (dB)
SCAN_CHANGE = 2.


# Search for possible signals
# Filtered to SCAN_BINS
# Peak must differ by SCAN_CHANGE from one of it's neighbouring bins
class Scan(object):
    def __init__(self, fs, samples, timing=None):
        self._fs = fs
        self._samples = samples
        self._timing = timing
        self._freqs = None
        self._levels = None
        self._peaks = None

    # Based on https://gist.github.com/endolith/250860
    def __peak_detect(self, spectrum):
        freqIndices = []

        indexPeak = 0
        levelMin = numpy.array(numpy.Inf, dtype=numpy.float32)
        levelMax = numpy.array(-numpy.Inf, dtype=numpy.float32)
        delta = numpy.array(SCAN_CHANGE, dtype=numpy.float32)

        findPeak = True
        for i in range(spectrum.size):
            level = spectrum[i]

            if level > levelMax:
                levelMax = level
                indexPeak = i
            if level < levelMin:
                levelMin = level

            if findPeak:
                if level <= levelMax - delta:
                    freqIndices.append(indexPeak)
                    levelMin = level
                    findPeak = False
            else:
                if level >= levelMin + delta:
                    levelMax = level
                    indexPeak = i
                    findPeak = True

        return freqIndices

    def search(self):
        if self._samples.size < SCAN_BINS:
            Utils.error('Sample too short')

        if self._timing is not None:
            self._timing.start('Scan')

        f, l = psd(self._samples, SCAN_BINS, self._fs)

        decibels = 10 * numpy.log10(l)

        freqIndices = self.__peak_detect(decibels)

        self._freqs = f
        self._levels = decibels
        self._peaks = decibels[freqIndices]
        freqs = f[freqIndices]

        if self._timing is not None:
            self._timing.stop()

        return freqs

    def get_spectrum(self):
        return self._freqs, self._levels

    def get_peaks(self):
        return self._peaks


if __name__ == '__main__':
    print 'Please run harrier.py'
    exit(1)
