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
from scipy.signal._peak_finding import find_peaks_cwt
from scipy.signal.spectral import welch

from harrier.constants import SAMPLE_RATE
from harrier.utils import Utils


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

    def search(self, fast):
        if self._samples.size < SCAN_BINS:
            Utils.error('Sample too short')

        if self._timing is not None:
            self._timing.start('Scan')

        f, l = welch(self._samples, nperseg=SCAN_BINS,
                     noverlap=-64 * 1024)
        f *= SAMPLE_RATE

        decibels = 10 * numpy.log10(l)

        if fast:
            diff = numpy.diff(decibels)
            # Peaks
            peakIndices = (numpy.diff(numpy.sign(diff)) < 0).nonzero()[0] + 1
            # Changes above SCAN_CHANGE
            threshPos = numpy.where((diff > SCAN_CHANGE))[0] + 1
            threshNeg = numpy.where((diff < -SCAN_CHANGE))[0]
            threshIndices = numpy.union1d(threshPos, threshNeg)
            # Peaks above SCAN_CHANGE
            signalIndices = numpy.where(numpy.in1d(peakIndices,
                                                   threshIndices))[0]
            freqIndices = peakIndices[signalIndices]
        else:
            freqIndices = find_peaks_cwt(decibels,
                                         numpy.arange(1, 4),
                                         min_snr=SCAN_CHANGE)

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
