#! /usr/bin/env python

import argparse
import os
import re
import sys
import time

import matplotlib
from collections import OrderedDict
matplotlib.use('TkAgg')
from matplotlib.patches import Rectangle
from matplotlib.ticker import EngFormatter
from matplotlib.widgets import RectangleSelector
import numpy
from scipy.io import wavfile

import matplotlib.pyplot as plt


#
# Sampling
#
# Sampling time per location (s)
SAMPLE_TIME = 4

#
# Scanning
#

# FFT bins used to scan
SCAN_BINS = 4096
# Peak level change (dB)
SCAN_CHANGE = 2.

#
# Detection
#

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


# Stores characteristics of detected pulses
class Pulse(object):
    # Index of the signal where it was found
    _signalNum = None
    # Modulation type
    _mod = None
    # Frequency (Hz)
    _freq = None
    # Number of pulses
    _count = None
    # Pulse rate (PPM)
    _rate = None
    # Pulse level
    _level = None
    # Pulse width
    _width = None

    def __init__(self, count, rate, level, width):
        self._count = count
        self._rate = rate
        self._level = level
        self._width = width

    def set_signal_number(self, signalNum):
        self._signalNum = signalNum

    def get_signal_number(self):
        return self._signalNum

    def set_frequency(self, freq):
        self._freq = freq

    def set_modulation(self, mod):
        self._mod = mod

    def get_modulation(self):
        return self._mod

    def get_description(self):
        desc = ('Freq: {:.3f}MHz Type: {}\n'
                'Count: {} Rate: {:.2f}PPM\n'
                'Level: {:.3f} Width: {:.1f}ms')
        desc = desc.format(self._freq / 1e6, self._mod,
                           self._count, self._rate,
                           self._level, self._width)

        return desc


# Basic timing
class Timing(object):
    _name = None
    _timings = OrderedDict()
    _paused = None

    def start(self, name):
        self._name = name
        if name not in self._timings:
            self._timings[name] = [0.] * 3

        self._timings[name][0] = time.clock()

    def pause(self):
        self._paused = time.clock()

    def resume(self):
        elapsed = time.clock() - self._paused
        self._timings[self._name][0] += elapsed

    def stop(self):
        elapsed = time.clock() - self._timings[self._name][0]
        self._timings[self._name][1] += elapsed
        self._timings[self._name][2] += 1

    def print_timings(self):
        formatTimings = '\t{:<8} {:>4d} {:>10.3f} {:>13.3f}'
        print 'Timings:'
        print '\t{:<8} {:>4} {:>10} {:>12}'.format('Routine', 'Runs', 'Total (s)', 'Average (ms)')
        timeTotal = 0
        for name, timing in self._timings.iteritems():
            if timing[2] != 0:
                timeTotal += timing[1]
                print formatTimings.format(name,
                                           int(timing[2]),
                                           timing[1],
                                           timing[1] * 1000. / timing[2])

        print '\t{:<8} {:>15.3f}s'.format('Total', timeTotal)


# Print error and exit
def error(error, fatal=True):
    if fatal:
        sys.exit(error)

    sys.stderr.write(error + '\n')


# Parse command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(prog='demod_test.py',
                                     description='Demodulation test')

    parser.add_argument('-i', '--info', help='Display summary info',
                        action='store_true')
    parser.add_argument('-s', '--spectrum', help='Display capture spectrum',
                        action='store_true')
    parser.add_argument('-c', '--scan', help='Display signal scan',
                        action='store_true')
    parser.add_argument('-e', '--edges', help='Display pulse edges',
                        action='store_true')
    parser.add_argument('-a', '--am', help='Display AM detection',
                        action='store_true')
    parser.add_argument('-b', '--block', help='Block to process',
                        type=int, default=0)
    parser.add_argument('-da', '--disableAm', help='Disable AM detection',
                        action='store_true')
    parser.add_argument('file', help='IQ wav file', nargs='?')
    args = parser.parse_args()

    if args.file is None:
        error('Please specify a file')
    if not os.path.isfile(args.file):
        error('Cannot find file')

    if args.am and args.disableAm:
        error('AM detection disabled - will not display graphs', False)

    return args


# Read data from wav file
def read_data(filename):
    name = os.path.split(filename)[1]

    print 'Loading:'
    print '\tLoading capture file: {}'.format(name)
    fs, data = wavfile.read(filename)

    if data.shape[1] != 2:
        error('Not an IQ file')
    if data.dtype != 'int16':
        error('Unexpected format')

    # Get baseband from filename
    regex = re.compile('_(\d+)kHz_IQ')
    matches = regex.search(name)
    if matches is not None:
        baseband = int(matches.group(1)) * 1000
    else:
        baseband = 0

    print '\tCapture sample rate (MSPS): {:.2f}'.format(fs / 1e6)
    print '\tCapture length (s): {:.2f}'.format(float(len(data)) / fs)

    # Scale data to +/-1
    data = data / 256.
    # Convert right/left to complex numbers
    iq = data[:, 1] + 1j * data[:, 0]

    return baseband, fs, iq


# Return ranges based on tolerance
def calc_tolerances(values, tolerance):
    valuesMin = [value * (100 - tolerance) / 100. for value in values]
    valuesMax = [value * (100 + tolerance) / 100. for value in values]
    return zip(valuesMax, valuesMin)


# Get levels of each frequency
def filter_frequencies(freqBins, magnitudes, frequencies):
    levels = []

    for freq in frequencies:
        # Closest bin
        fftBin = (numpy.abs(freqBins - freq)).argmin()
        level = magnitudes[fftBin]
        levels.append(level)

    return levels


# Calculate thresholds based on percentiles
def find_edges(edges, pulseWidths):
    minPulses = SAMPLE_TIME * min(PULSE_RATES) / 60.
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
def find_pulses(signal, negIndices, posIndices, pulseWidths):
    pulse = None
    length = signals.shape[1]
    # Find pulses of pulseWidths
    widthsFound = negIndices - posIndices
    # Ignore negative pulse widths:
    if numpy.any(widthsFound < 0):
        return None

    for wMax, wMin in pulseWidths:
        widthsValid = widthsFound[(widthsFound > wMin) & (widthsFound < wMax)]
        # Must have at least 2 pulses
        if widthsValid.size > 1:
            pulseValid = posIndices[:widthsValid.size]
            pulseRate = numpy.diff(pulseValid)
            pulseAvg = numpy.average(pulseRate)
            # Constant rate?
            maxDeviation = pulseAvg * PULSE_RATE_DEVIATION / 100.
            if numpy.std(pulseRate) < maxDeviation:
                # Calculate frequency
                freq = length / (pulseAvg * float(SAMPLE_TIME))
                rate = freq * 60
                # Limit to PULSE_RATES
                closest = min(PULSE_RATES, key=lambda x: abs(x - rate))
                if (abs(closest - rate)) < PULSE_RATE_TOL:
                    # Get pulse levels
                    level = 0
                    for posValid in range(len(pulseValid)):
                        pos = pulseValid[posValid]
                        width = widthsValid[posValid]
                        pulseSignal = signal[pos:pos + width - 1]
                        level += numpy.average(pulseSignal)
                    level /= len(pulseValid)
                    # Store valid pulse
                    pulse = Pulse(widthsValid.size,
                                  freq * 60.,
                                  level,
                                  width * SAMPLE_TIME * 1000. / length)
                    break

    return pulse


# Find tone ranges and return a pulse based on the signal
def find_tone(signal, indices, freqs):
    if not len(indices):
        return None, None

    sampleRate = signals.shape[1] / float(SAMPLE_TIME)
    periods = [sampleRate / freq for freq in freqs]
    periods = calc_tolerances(periods, TONE_TOL)

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
def find_am(signal, posIndices, negIndices, showAm):
    # Find +ve cycles
    freq, amPos = find_tone(signal, posIndices, TONES)
    if freq is None:
        return None, [], []
    # Find matching -ve cycle
    freq, amNeg = find_tone(signal, negIndices, [freq])
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

    if showAm:
        timing.pause()
        x = numpy.linspace(0, SAMPLE_TIME, signal.size)
        ax = plt.subplot(111)
        plt.title('AM Detection')
        plt.plot(x, am, label='{:.1f}Hz'.format(freq))
        xScale = float(SAMPLE_TIME) / am.size
        labelPos = '+ve'
        labelNeg = '-ve'
        for posIndex in amPosIndices:
            plt.axvline((posIndex + 1) * xScale, color='g', label=labelPos)
            labelPos = None
        for negIndex in amNegIndices:
            plt.axvline((negIndex + 1) * xScale, color='r', label=labelNeg)
            labelNeg = None
        plt.xlabel('Time (s)')
        plt.ylabel('Level')
        plt.grid()
        plt.legend(prop={'size': 10}, framealpha=0.5)
        _selector = RectangleSelector(ax, selection_time,
                                      drawtype='box', useblit=True)
        plt.show()
        timing.resume()

    return am, amPosIndices, amNegIndices


# Scan for possible signals
# Filtered to SCAN_BINS
# Peak must differ by SCAN_CHANGE from one of it's neighbouring bins
def scan(baseband, fs, samples, showScan):
    if samples.size < SCAN_BINS:
        error('Sample too short')

    timing.start('Scan')

    # TODO: implement PSD in Numpy rather than add another import
    l, f = matplotlib.mlab.psd(samples, SCAN_BINS, Fs=fs)
    decibels = 10 * numpy.log10(l)

    diff = numpy.diff(decibels)
    # Peaks
    peakIndices = (numpy.diff(numpy.sign(diff)) < 0).nonzero()[0] + 1
    # Changes above SCAN_CHANGE
    threshIndices = numpy.where((diff > SCAN_CHANGE) | (diff < -SCAN_CHANGE))[0]
    # Peaks above SCAN_CHANGE
    signalIndices = numpy.where(numpy.in1d(peakIndices, threshIndices))[0]
    freqIndices = peakIndices[signalIndices]

    freqs = f[freqIndices]
    levels = decibels[freqIndices]

    timing.stop()

    # Plot results
    if showScan:
        _fig, ax = plt.subplots()
        ax.set_title('Scan')
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Level')
        ax.xaxis.set_major_formatter(EngFormatter(places=1))
        ax.grid()

        ax.plot(f + baseband, decibels, label='Signal')
        ax.plot(freqs + baseband, levels,
                linestyle='None', marker='o',
                color='r', label='Peaks')
        plt.legend(prop={'size': 10}, framealpha=0.8)
        # Add a rectangle selector for measurements
        _selector = RectangleSelector(ax, selection_freq,
                                      drawtype='box', useblit=True)
        plt.show()

    return freqs


# Analyse blocks from capture
def demod(fs, samples, frequencies):
    chunks = samples.size / DEMOD_BINS
    if chunks == 0:
        error('Sample time too long')

    signals = numpy.empty((chunks, len(frequencies)))

    # Split samples into chunks
    for chunkNum in range(chunks):
        timing.start('Demod')

        chunkStart = chunkNum * DEMOD_BINS
        chunk = samples[chunkStart:chunkStart + DEMOD_BINS]

        # Analyse chunk
        fft = numpy.fft.fft(chunk) / DEMOD_BINS
        mags = numpy.absolute(fft)
        freqBins = numpy.fft.fftfreq(DEMOD_BINS, 1. / fs)
        levels = filter_frequencies(freqBins, mags, frequencies)
        signals[chunkNum] = levels

        timing.stop()

    return signals


# Smooth signal & remove DC offset
def smooth(signals, boxLen):
    box = numpy.ones(boxLen) / float(boxLen)

    for signalNum in range(signals.shape[0]):
        signals[signalNum] = numpy.convolve(signals[signalNum], box, mode='same')
        signals[signalNum] -= numpy.average(signals[signalNum])


# Find pulses and their frequency
def detect(baseband, frequencies, signals, showEdges, showAm, disableAm):
    pulses = []

    # Calculate valid pulse widths with PULSE_WIDTH_TOL tolerance
    sampleRate = signals.shape[1] / float(SAMPLE_TIME)
    pulseWidths = [width * sampleRate for width in sorted(PULSE_WIDTHS)]
    pulseWidths = calc_tolerances(pulseWidths, PULSE_WIDTH_TOL)

    signalNum = 0
    for signal in signals:
        timing.start('Detect')

        edge = numpy.diff(signal)
        threshPos, threshNeg, posIndices, negIndices = find_edges(edge, pulseWidths)

        # Find CW pulses
        pulse = find_pulses(signal,
                            negIndices, posIndices,
                            pulseWidths)

        # Find AM pulses
        if pulse is None:
            if not disableAm:
                am, posIndices, negIndices = find_am(signal,
                                                     posIndices, negIndices,
                                                     showAm)
                if am is not None:
                    pulse = find_pulses(am, negIndices, posIndices, pulseWidths)
                    if pulse is not None:
                        pulse.set_modulation('AM')
        else:
            pulse.set_modulation('CW')

        if pulse is not None:
            pulse.set_signal_number(signalNum)
            pulse.set_frequency(frequencies[signalNum] + baseband)
            pulses.append(pulse)

        timing.stop()

        # Display differentiated signal with thresholds (-e)
        if showEdges:
            x = numpy.linspace(0, SAMPLE_TIME, edge.size)
            ax = plt.subplot(111)
            title = 'Signal Edges ({})'.format(signalNum + 1)
            if pulse is not None:
                title += ' (Pulses Found - {})'.format(pulse.get_modulation())
            plt.title(title)
            plt.grid()
            label = '{:.3f}MHz'.format((baseband + frequencies[signalNum]) / 1e6)
            plt.plot(x, edge, label=label)
            plt.axhline(threshPos, color='g', label='+ve')
            plt.axhline(threshNeg, color='r', label='-ve')
            xScale = float(SAMPLE_TIME) / edge.size
            for posIndex in posIndices:
                plt.axvline((posIndex + 1) * xScale, color='g')
            for negIndex in negIndices:
                plt.axvline((negIndex + 1) * xScale, color='r')
            plt.legend(prop={'size': 10}, framealpha=0.5)
            # Add a rectangle selector for measurements
            _selector = RectangleSelector(ax, selection_time,
                                          drawtype='box', useblit=True)
            plt.show()

        signalNum += 1

    return pulses


# Display dragged rectangle
def selection_time(eventClick, eventRelease):
    xStart = eventClick.xdata
    xEnd = eventRelease.xdata
    yStart = eventClick.ydata
    yEnd = eventRelease.ydata
    width = xEnd - xStart
    height = yEnd - yStart

    axes = eventClick.inaxes

    draw_selection(axes, xStart, yStart, width, height)

    dx = 'dT: {:.1f}ms'.format(abs(width) * 1000.)
    dy = 'dL: {:.4f}'.format(abs(height))
    text = 'Selection:\n\n' + dx + '\n' + dy
    draw_text(axes, text)


def selection_freq(eventClick, eventRelease):
    xStart = eventClick.xdata
    xEnd = eventRelease.xdata
    yStart = eventClick.ydata
    yEnd = eventRelease.ydata
    width = xEnd - xStart
    height = yEnd - yStart

    axes = eventClick.inaxes

    draw_selection(axes, xStart, yStart, width, height)

    dx = 'df: {:.1f}kHz'.format(abs(width) / 1000.)
    dy = 'dL: {:.4f}dB'.format(abs(height))
    text = 'Selection:\n\n' + dx + '\n' + dy
    draw_text(axes, text)


# Draw selection rectangle
def draw_selection(axes, x, y, width, height):
    remove_child(axes, 'rectangeSelection')

    rectangle = Rectangle((x, y), width, height,
                          alpha=0.5,
                          facecolor='grey',
                          edgecolor='black',
                          gid='rectangeSelection')
    axes.add_patch(rectangle)


# Draw text in upper right
def draw_text(axes, text):
    remove_child(axes, 'boxText')

    bbox = dict(alpha=0.8, facecolor='w')
    plt.text(0.02, 0.98, text, size=10,
             transform=axes.transAxes,
             verticalalignment='top',
             bbox=bbox,
             gid='boxText')
    plt.draw()


# Remove child from plot
def remove_child(axes, gid):
    for child in axes.get_children():
        if child.get_gid() is not None:
            if child.get_gid() is gid:
                child.remove()


# Main entry point
if __name__ == '__main__':
    timing = Timing()

    # Parse command line arguments
    args = parse_arguments()

    # Read source file
    baseband, fs, iq = read_data(args.file)

    if args.info:
        info = ('Info:\n'
                '\tBlock size: {}s\n'
                '\tScan resolution {:.2f}Hz\n'
                '\tDemod resolution {:.2f}Hz ({:.2f}ms)\n')
        print (info).format(SAMPLE_TIME,
                            float(fs) / SCAN_BINS,
                            float(fs) / DEMOD_BINS, DEMOD_BINS * 1e3 / float(fs))

    # Show spectrum of entire plot (-s)
    if args.spectrum:
        ax = plt.subplot(111)
        plt.psd(iq, NFFT=4096, Fs=fs)
        plt.title('Spectrum')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Level')
        plt.grid()
        _selector = RectangleSelector(ax, selection_freq,
                                      drawtype='box', useblit=True)
        plt.show()

    sampleSize = fs * SAMPLE_TIME
    sampleBlocks = iq.size / sampleSize
    if sampleBlocks == 0:
        error('Capture too short')

    print 'Analysis:'
    # Split input file into SAMPLE_TIME seconds blocks
    for blockNum in range(sampleBlocks):
        if args.block > 0 and args.block != blockNum + 1:
            continue

        print '\tBlock {}/{}'.format(blockNum + 1, sampleBlocks)
        sampleStart = blockNum * sampleSize
        samples = iq[sampleStart:sampleStart + sampleSize]

        frequencies = scan(baseband, fs, samples, args.scan)

        print '\t\tSignals to demodulate: {}'.format(len(frequencies))

        # Demodulate
        signals = demod(fs, samples, frequencies).T

        # Reduce noise
        smooth(signals, 4)
        # Detect pulses
        pulses = detect(baseband, frequencies, signals,
                        args.edges, args.am, args.disableAm)

        # Plot results
        ax = plt.subplot(111)
        plt.title('Block {}'.format(blockNum + 1))
        plt.xlabel('Time (s)')
        plt.ylabel('Level')
        plt.grid()

        # Create the x axis time points
        startTime = blockNum * SAMPLE_TIME
        x = numpy.linspace(startTime, startTime + SAMPLE_TIME, signals.shape[1])

        # Plot the signals
        for pulse in pulses:
            signalNum = pulse.get_signal_number()
            plt.plot(x, signals[signalNum], label=pulse.get_description())

        if len(pulses):
            plt.legend(prop={'size': 10}, framealpha=0.5)

        # Add a rectangle selector for measurements
        _selector = RectangleSelector(ax, selection_time,
                                      drawtype='box', useblit=True)
        plt.show()

    timing.print_timings()

    print 'Done'
