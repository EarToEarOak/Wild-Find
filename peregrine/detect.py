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
import collar
from constants import SAMPLE_TIME


class Detect(object):
    # Size of each block to analyse
    DEMOD_BINS = 4096
    # Valid pulse widths (s)
    PULSE_WIDTHS = [25e-3, 64e-3]
    # Pulse width tolerance (+/- %)
    PULSE_WIDTH_TOL = 25
    # Maximum pulse rate deviation (%)
    PULSE_RATE_DEVIATION = 2
    # Valid pulse rates (Pulses per minute)
    PULSE_RATES = [40, 60, 80]
    # Pulse rate tolerance (+/- Pulses per minute)
    PULSE_RATE_TOL = 10
    # Valid AM tones (Hz)
    TONES = [260]
    # Tolerance of AM tones (%)
    TONE_TOL = 10

    def __init__(self, fs, samples, frequencies, timing=None, debug=None):
        self._fs = fs
        self._samples = samples
        self._frequencies = frequencies
        self._signals = []
        self._timing = timing
        self._debug = debug

    # Get levels of each frequency
    def filter_frequencies(self, freqBins, magnitudes):
        levels = []

        for freq in self._frequencies:
            # Closest bin
            fftBin = (numpy.abs(freqBins - freq)).argmin()
            level = magnitudes[fftBin]
            levels.append(level)

        return levels

    # Calculate thresholds based on percentiles
    def __find_edges(self, edges, pulseWidths):
        minPulses = SAMPLE_TIME * min(Detect.PULSE_RATES) / 60.
        minHigh = minPulses * min(min(pulseWidths)) / 1e3
        threshold = 1 - (minHigh / SAMPLE_TIME)
        threshold *= 100

        t1 = numpy.percentile(edges[edges > 0], threshold)
        t2 = numpy.mean(edges[edges > 0])
        t3 = numpy.percentile(edges[edges < 0], 100 - threshold)
        t4 = numpy.mean(edges[edges < 0])
        threshPos = t2 + (t1 - t2) / 2
        threshNeg = t4 + (t3 - t4) / 2

        # Mark edges
        pos = edges > threshPos
        neg = edges < threshNeg
        # Find edge indices
        posIndices = numpy.where((pos[1:] == True) & (pos[:-1] == False))[0]
        negIndices = numpy.where((neg[1:] == True) & (neg[:-1] == False))[0]
        minSize = min(len(posIndices), len(negIndices))
        posIndices = posIndices[:minSize]
        negIndices = negIndices[:minSize]

        return threshPos, threshNeg, posIndices, negIndices

    # Find pulses
    def __find_pulses(self, signal, negIndices, posIndices, pulseWidths):
        pulse = None
        length = signal.size
        # Find pulses of pulseWidths
        widthsFound = negIndices - posIndices
        # Ignore negative pulse widths:
        if numpy.any(widthsFound < 0):
            if self._debug is not None and self._debug.verbose:
                Utils.error('Negative widths found', False)
            return None

        for wMax, wMin in pulseWidths:
            widthsValid = widthsFound[(widthsFound > wMin) &
                                      (widthsFound < wMax)]
            # Must have at least 2 pulses
            if widthsValid.size > 1:
                pulseValid = posIndices[:widthsValid.size]
                pulseRate = numpy.diff(pulseValid)
                pulseAvg = numpy.average(pulseRate)
                # Constant rate?
                maxDeviation = pulseAvg * Detect.PULSE_RATE_DEVIATION / 100.
                if numpy.std(pulseRate) < maxDeviation:
                    # Calculate frequency
                    freq = length / (pulseAvg * float(SAMPLE_TIME))
                    rate = freq * 60
                    # Limit to PULSE_RATES
                    closest = min(Detect.PULSE_RATES,
                                  key=lambda x: abs(x - rate))
                    if (abs(closest - rate)) < Detect.PULSE_RATE_TOL:
                        # Get pulse levels
                        level = 0
                        for posValid in range(len(pulseValid)):
                            pos = pulseValid[posValid]
                            width = widthsValid[posValid]
                            pulseSignal = signal[pos:pos + width - 1]
                            level += numpy.average(pulseSignal)
                        level /= len(pulseValid)
                        # Store valid pulse
                        pulse = collar.Collar(widthsValid.size,
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
                Utils.error('Only found {} pulses'.format(widthsValid.size),
                            False)

        return pulse

    # Find tone ranges and return a pulse based on the signal
    def __find_tone(self, signal, indices, freqs):
        if not len(indices):
            return None, None

        sampleRate = signal.size / float(SAMPLE_TIME)
        periods = [sampleRate / freq for freq in freqs]
        periods = Utils.calc_tolerances(periods, Detect.TONE_TOL)

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
        pulse = numpy.zeros((signal.size))
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
        freq, amPos = self.__find_tone(signal, posIndices, Detect.TONES)
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
    def __detect(self, signals):
        collars = []

        # Calculate valid pulse widths with PULSE_WIDTH_TOL tolerance
        sampleRate = signals.shape[1] / float(SAMPLE_TIME)
        pulseWidths = [width * sampleRate for width in sorted(Detect.PULSE_WIDTHS)]
        pulseWidths = Utils.calc_tolerances(pulseWidths,
                                            Detect.PULSE_WIDTH_TOL)

        signalNum = 0
        for signal in signals:
            if self._timing is not None:
                self._timing.start('Detect')

            self._signals.append(signal)
            edge = numpy.diff(signal)
            (threshPos, threshNeg,
             posIndices, negIndices) = self.__find_edges(edge, pulseWidths)

            # Find CW collars
            pulse = self.__find_pulses(signal,
                                       negIndices, posIndices,
                                       pulseWidths)

            # Find AM collars
            if pulse is None:
                if self._debug is not None and not self._debug.disableAm:
                    am, posIndices, negIndices = self.__find_am(signal,
                                                                posIndices,
                                                                negIndices)
                if self._debug is not None:
                    if not self._debug.disableAm and am is not None:
                        pulse = self.__find_pulses(am,
                                                   negIndices, posIndices,
                                                   pulseWidths)
                        if pulse is not None:
                            pulse.mod = collar.AM
            else:
                pulse.mod = collar.CW

            if pulse is not None:
                pulse.signalNum = signalNum
                pulse.freq = self._frequencies[signalNum]
                collars.append(pulse)

            if self._timing is not None:
                self._timing.stop()

            if self._debug is not None:
                self._debug.callback_edge(edge, signalNum, pulse,
                                          self._frequencies,
                                          threshPos, threshNeg,
                                          posIndices, negIndices)

            signalNum += 1

        return collars

    # Analyse blocks from capture
    def __demod(self):
        chunks = self._samples.size / Detect.DEMOD_BINS
        if chunks == 0:
            Utils.error('Sample time too long')

        signals = numpy.empty((chunks, len(self._frequencies)))

        # Split samples into chunks
        for chunkNum in range(chunks):
            if self._timing is not None:
                self._timing.start('Demod')

            chunkStart = chunkNum * Detect.DEMOD_BINS
            chunk = self._samples[chunkStart:chunkStart + Detect.DEMOD_BINS]

            # Analyse chunk
            fft = numpy.fft.fft(chunk) / Detect.DEMOD_BINS
            mags = numpy.absolute(fft)
            freqBins = numpy.fft.fftfreq(Detect.DEMOD_BINS, 1. / self._fs)
            levels = self.filter_frequencies(freqBins, mags)
            signals[chunkNum] = levels

            if self._timing is not None:
                self._timing.stop()

        signals = signals.T
        self.__smooth(signals, 4)

        return signals

    def search(self):
        signals = self.__demod()
        return self.__detect(signals)

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
