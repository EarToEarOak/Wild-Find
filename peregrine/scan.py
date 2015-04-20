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

import numpy

from utils import Utils
from matplotlib.mlab import psd

# Search for possible signals
# Filtered to SCAN_BINS
# Peak must differ by SCAN_CHANGE from one of it's neighbouring bins


class Scan(object):
    # FFT bins used to search
    SCAN_BINS = 4096
    # Peak level change (dB)
    SCAN_CHANGE = 2.

    def __init__(self, fs, samples, timing=None):
        self._fs = fs
        self._samples = samples
        self._timing = timing
        self._freqs = None
        self._levels = None
        self._peaks = None

    def search(self):
        if self._samples.size < Scan.SCAN_BINS:
            Utils.error('Sample too short')

        if self._timing is not None:
            self._timing.start('Scan')

        # TODO: implement PSD in Numpy rather than add another import
        l, f = psd(self._samples, Scan.SCAN_BINS, Fs=self._fs)
        decibels = 10 * numpy.log10(l)

        diff = numpy.diff(decibels)
        # Peaks
        peakIndices = (numpy.diff(numpy.sign(diff)) < 0).nonzero()[0] + 1
        # Changes above SCAN_CHANGE
        threshIndices = numpy.where((diff > Scan.SCAN_CHANGE) |
                                    (diff < -Scan.SCAN_CHANGE))[0]
        # Peaks above SCAN_CHANGE
        signalIndices = numpy.where(numpy.in1d(peakIndices, threshIndices))[0]
        freqIndices = peakIndices[signalIndices]

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
