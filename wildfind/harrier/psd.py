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

import numpy
from scipy import fftpack


# A slightly optimised version of psd from http://matplotlib.org/
def psd(samples, nfft, fs):

    window = numpy.hanning(nfft).astype(numpy.float32)

    step = nfft + (64 * 1024)
    indices = numpy.arange(0, len(samples) - nfft + 1, step)
    length = len(indices)
    levels = numpy.zeros((nfft, length), numpy.complex64)

    for i in range(length):
        chunk = samples[indices[i]:indices[i] + nfft]
        chunk = window * chunk
        fft = fftpack.fft(chunk, overwrite_x=True)
        levels[:, i] = numpy.conj(fft[:nfft]) * fft[:nfft]

    levels = levels.mean(axis=1)
    levels = numpy.absolute(levels)
    levels = numpy.concatenate((levels[nfft / 2:], levels[:nfft / 2]))

    freqs = float(fs) / nfft * numpy.arange(nfft)
    freqs = numpy.concatenate((freqs[nfft / 2:] - fs, freqs[:nfft / 2]))

    return freqs, levels


if __name__ == '__main__':
    print 'Please run harrier.py'
    exit(1)
