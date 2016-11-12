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

import itertools
import operator

import numpy
from scipy import fftpack

from harrier import collar
from harrier.constants import SAMPLE_TIME
from harrier.utils import Utils


# Size of each block to analyse
DEMOD_BINS = 4096
# Valid pulse widths (s)
PULSE_WIDTHS = [10e-3, 25e-3, 64e-3]
# Pulse width tolerance (+/- %)
PULSE_WIDTH_TOL = 75
# Minimum high to low level ratio
PULSE_LEVEL_RATIO = 5
# Maximum pulse rate deviation (%)
PULSE_RATE_DEVIATION = 15
# Valid pulse rates (Pulses per minute)
PULSE_RATES = [40, 60, 80]
# Pulse rate tolerance (+/- Pulses per minute)
PULSE_RATE_TOL = 10
# Valid AM tones (Hz)
TONES = [260]
# Tolerance of AM tones (%)
TONE_TOL = 10
# Tolerance of ghosts (Hz)
GHOST_RATE_TOL = 5
# Correlation of ghosts (%)
GHOST_CORR = 33
# Channel spacing (Hz)
CHANNEL_SPACE = 20e3


class Detect(object):
    def __init__(self, fs, samples, frequencies, timing=None, debug=None):
        self._fs = fs
        self._samples = samples
        self._frequencies = frequencies
        self._signals = []
        self._timing = timing
        self._debug = debug

    # Find pulse edges
    def __find_edges(self, signals, pulseWidths):
        minPulses = SAMPLE_TIME * min(PULSE_RATES) / 60.
        minHigh = minPulses * min(min(pulseWidths)) / 1e3
        threshold = 1 - (minHigh / SAMPLE_TIME)
        threshold *= 100

        t1 = numpy.percentile(signals, threshold)
        t2 = numpy.percentile(signals, threshold - 5)
        offset = (t1 - t2) / 3.
        threshHigh = t1 - offset
        threshLow = t2 + offset

        high = signals >= threshHigh
        low = signals <= threshLow
        both = high | low
        indicesBoth = numpy.nonzero(both)[0]
        counter = numpy.cumsum(both)
        edges = numpy.where(counter, high[indicesBoth[counter - 1]], False)

        indicesEdge = numpy.nonzero(numpy.diff(edges))[0]
        indicesPos = indicesEdge[0::2]
        indicesNeg = indicesEdge[1::2]

        edgeDiff = abs(indicesPos.size - indicesNeg.size)
        if edgeDiff > 1:
            return (threshHigh, threshLow,
                    numpy.array([]), numpy.array([]))
        elif edgeDiff == 1:
            minSize = min(len(indicesPos), len(indicesNeg))
            indicesPos = indicesPos[:minSize]
            indicesPos = indicesPos[:minSize]

        return (threshHigh, threshLow,
                indicesPos, indicesNeg)

    # Find pulses
    def __find_pulses(self, signal, negIndices, posIndices, pulseWidths):
        pulse = None
        length = signal.size
        # Find pulses of pulseWidths
        widths = negIndices - posIndices

        for wMax, wMin in pulseWidths:
            posValid = numpy.where((widths > wMin) & (widths < wMax))[0]
            # Must have at least 2 pulses
            if posValid.size > 1 and posValid.size == widths.size:
                pulseValid = posIndices[posValid]
                pulseRate = numpy.diff(pulseValid)
                pulseAvg = numpy.average(pulseRate)
                # Constant rate?
                maxDeviation = pulseAvg * PULSE_RATE_DEVIATION / 100.
                if numpy.std(pulseRate) < maxDeviation:
                    # Calculate frequency
                    freq = length / (pulseAvg * float(SAMPLE_TIME))
                    rate = freq * 60
                    # Limit to PULSE_RATES
                    closest = min(PULSE_RATES,
                                  key=lambda x: abs(x - rate))
                    if (abs(closest - rate)) < PULSE_RATE_TOL:
                        # Get pulse levels
                        level = 0
                        for posValid in range(len(pulseValid)):
                            pos = pulseValid[posValid]
                            width = widths[posValid]
                            pulseSignal = signal[pos:pos + width - 1]
                            level += numpy.average(pulseSignal)
                        level /= len(pulseValid)
                        # Store valid pulse
                        pulse = collar.Collar(widths.size,
                                              freq * 60.,
                                              level,
                                              width * SAMPLE_TIME * 1000. / length)
                        break
                    elif self._debug is not None and self._debug.verbose:
                        Utils.error('Invalid rate {:.1f}PPM'.format(rate),
                                    False)
                elif self._debug is not None and self._debug.verbose:
                    msg = 'Collar rate deviation {:.1f} >= {:.1f}ms'
                    msg = msg.format(1000 * numpy.std(pulseRate) * SAMPLE_TIME / length,
                                     1000 * maxDeviation * SAMPLE_TIME / length)
                    Utils.error(msg, False)
            elif self._debug is not None and self._debug.verbose:
                Utils.error('Only found {} pulses'.format(posValid.size),
                            False)

        return pulse

    # Find tone ranges and return a pulse based on the signal
    def __find_tone(self, signal, indices, freqs):
        if not len(indices):
            return None, None

        sampleRate = signal.size / float(SAMPLE_TIME)
        periods = [sampleRate / freq for freq in freqs]
        periods = Utils.calc_tolerances(periods, TONE_TOL)

        # Edge widths
        if indices[0] != 0:
            indices = numpy.insert(indices, 0, 0)
        widths = numpy.diff(indices)

        # Count valid widths for each period
        counts = []
        for maxPeriod, minPeriod in periods:
            valid = (widths > minPeriod) & (widths < maxPeriod)
            counts.append(numpy.sum(valid))
        # Find maximum
        maxCounts = max(counts)
        if maxCounts == 0:
            if self._debug is not None and self._debug.verbose:
                Utils.error('No tone found', False)
            return None, None
        maxPos = counts.index(maxCounts)
        maxPeriod, minPeriod = periods[maxPos]
        # Matching widths
        periodsValid = (widths > minPeriod) & (widths < maxPeriod)
        periodAvg = numpy.average(widths[periodsValid])
        freq = sampleRate / periodAvg

        # Create pulses from signal
        pulse = numpy.zeros((signal.size), dtype=numpy.float16)
        pos = 0
        for i in range(widths.size):
            width = widths[i]
            valid = periodsValid[i]
            signalPos = indices[i]
            level = numpy.average(signal[signalPos:signalPos + width])
            level = abs(level)
            pulse[pos:pos + width].fill(valid * level)
            pos += width

        return freq, pulse

    # Find AM signal
    def __find_am(self, signal, posIndices, negIndices):
        # Find +ve cycles
        freq, amPos = self.__find_tone(signal, posIndices, TONES)
        if freq is None:
            return None, [], []
        # Find matching -ve cycle
        freq, amNeg = self.__find_tone(signal, negIndices, [freq])
        if freq is None:
            return None, [], []
        # Average +/- ve pulses
        am = (amPos + amNeg) / 2.

        # Find edges
        amPosIndices = numpy.where((am[1:] != 0) & (am[:-1] == 0))[0]
        amNegIndices = numpy.where((am[1:] == 0) & (am[:-1] != 0))[0]
        minSize = min(len(amPosIndices), len(amNegIndices))
        amPosIndices = amPosIndices[:minSize]
        amNegIndices = amNegIndices[:minSize]

        if self._debug is not None:
            self._timing.pause()
            self._debug.callback_am(signal, am, freq,
                                    amPosIndices, amNegIndices)
            self._timing.resume()

        return am, amPosIndices, amNegIndices

    # Smooth signal & remove DC offset
    def __smooth(self, signals, boxLen):
        box = numpy.ones(boxLen) / float(boxLen)

        for signalNum in range(signals.shape[0]):
            signals[signalNum] = numpy.convolve(signals[signalNum],
                                                box, mode='same')
            signals[signalNum] -= numpy.average(signals[signalNum])

    # Find pulses and their frequency
    def __detect(self, signals, baseband):
        collars = []

        # Calculate valid pulse widths with PULSE_WIDTH_TOL tolerance
        sampleRate = signals.shape[1] / float(SAMPLE_TIME)
        pulseWidths = [width * sampleRate for width in sorted(PULSE_WIDTHS)]
        pulseWidths = Utils.calc_tolerances(pulseWidths,
                                            PULSE_WIDTH_TOL)

        signalNum = 0
        for signal in signals:
            if self._timing is not None:
                self._timing.start('Detect')

            self._signals.append(signal)

            (threshPos, threshNeg,
             posIndices, negIndices) = self.__find_edges(signal, pulseWidths)

            # Find CW collars
            pulse = self.__find_pulses(signal,
                                       negIndices, posIndices,
                                       pulseWidths)

            # Find AM collars
            if pulse is None:
                if self._debug is not None and not self._debug.disableAm:
                    am, posIndicesAm, negIndicesAm = self.__find_am(signal,
                                                                    posIndices,
                                                                    negIndices)
                if self._debug is not None:
                    if not self._debug.disableAm and am is not None:
                        pulse = self.__find_pulses(am,
                                                   negIndicesAm, posIndicesAm,
                                                   pulseWidths)
                        if pulse is not None:
                            pulse.mod = collar.AM
                            posIndices = posIndicesAm
                            negIndices = negIndicesAm
            else:
                pulse.mod = collar.CW

            if pulse is not None:
                pulse.signalNum = signalNum
                freq = self._frequencies[signalNum] + baseband
                freq = int(round(freq / CHANNEL_SPACE) * CHANNEL_SPACE)
                pulse.freq = freq
                collars.append(pulse)

            if self._timing is not None:
                self._timing.stop()

            if self._debug is not None:
                self._debug.callback_edge(baseband, signal, signalNum, pulse,
                                          self._frequencies,
                                          threshPos, threshNeg,
                                          posIndices, negIndices)

            signalNum += 1

        return collars

    # Demodulate blocks from capture
    def __demod(self):
        chunks = self._samples.size / DEMOD_BINS
        if chunks == 0:
            Utils.error('Sample time too long')

        signals = numpy.empty((chunks, len(self._frequencies)),
                              dtype=numpy.float16)

        # Split samples into chunks
        freqBins = fftpack.fftfreq(DEMOD_BINS, 1. / self._fs)
        freqInds = freqBins.argsort()

        for chunkNum in range(chunks):
            if self._timing is not None:
                self._timing.start('Demod')

            chunkStart = chunkNum * DEMOD_BINS
            chunk = self._samples[chunkStart:chunkStart + DEMOD_BINS]

            # Analyse chunk
            fft = fftpack.fft(chunk, overwrite_x=True)
            fft /= DEMOD_BINS
            mags = numpy.absolute(fft)
            bins = numpy.searchsorted(freqBins[freqInds],
                                      self._frequencies)
            levels = mags[freqInds][bins]
            signals[chunkNum] = levels

            if self._timing is not None:
                self._timing.stop()

        signals = signals.T
        self.__smooth(signals, 4)

        return signals

    def __correlate(self, a, v):
        # Normalise
        if self._timing is not None:
            self._timing.start('Correl')
        a = (a - numpy.mean(a)) / (numpy.std(a, dtype=numpy.float32) * len(a))
        v = (v - numpy.mean(v)) / numpy.std(v, dtype=numpy.float32)
        corr = numpy.correlate(a, v)
        if self._timing is not None:
            self._timing.stop()

        return corr[0] > (GHOST_CORR / 100.)

    def __remove_ghosts(self, signals, detected):
        if len(detected) < 2:
            return

        # Split into groups based on rate
        rates = [collar.rate for collar in detected]
        rates.sort()
        df = numpy.diff(rates)
        pos = numpy.where(df > GHOST_RATE_TOL)[0] + 1
        groups = numpy.split(rates, pos)

        # Try all combinations
        toRemove = []
        for group in groups:
            collars = [collar for collar in detected
                       if collar.rate in group]
            collars.sort(key=operator.attrgetter('level'), reverse=True)
            combinations = itertools.combinations(collars, 2)
            for combo in combinations:
                # Test if signals correlate
                corr = self.__correlate(signals[combo[0].signalNum],
                                        signals[combo[1].signalNum])
                if corr:
                    toRemove.append(combo[1])

        toRemove = set(toRemove)
        for collar in toRemove:
            detected.remove(collar)

        if self._debug is not None and self._debug.verbose:
            print '\tRemoved {} ghosts'.format(len(toRemove))

    def search(self, baseband):
        if not len(self._frequencies):
            return []
        signals = self.__demod()
        detected = self.__detect(signals, baseband)
        self.__remove_ghosts(signals, detected)

        return detected

    def get_signals(self):
        return self._signals


class DetectDebug(object):
    def __init__(self, edges, am, disableAm, verbose):
        self.edges = edges
        self.am = am
        self.disableAm = disableAm
        self.verbose = verbose
        self._callbackEdge = None
        self._callbackAm = None

    def set_callbacks(self, edge=None, am=None):
        self._callbackEdge = edge
        self._callbackAm = am

    def callback_edge(self, *args):
        if self._callbackEdge is not None:
            self._callbackEdge(*args)

    def callback_am(self, *args):
        if self._callbackAm is not None:
            self._callbackAm(*args)


# Convert IQ stream to complex
def stream_to_complex(stream):
    bytes_np = numpy.ctypeslib.as_array(stream)
    iq = bytes_np.astype(numpy.float32).view(numpy.complex64)
    iq /= 255 / 2
    iq -= 1 + 1j

    return iq


if __name__ == '__main__':
    print 'Please run harrier.py'
    exit(1)
