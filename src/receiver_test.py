#! /usr/bin/env python

import argparse
import os
import re
import sys
import time

import matplotlib
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
# Pulse threshold (%)
PULSE_THRESHOLD = 99.5
# Valid pulse widths (s)
PULSE_WIDTHS = [25e-3, 64e-3]
# Pulse width tolerance (+/- %)
PULSE_WIDTH_TOL = 20
# Valid pulse rates (Pulses per minute)
PULSE_RATES = [40, 60, 80]
# Pulse rate tolerance (+/- Pulses per minute)
PULSE_RATE_TOL = 10


# Stores characteristics of detected pulses
class Pulse(object):
    # Index of the signal where it was found
    _signalNum = None
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

    def __init__(self, signalNum, freq, count, rate, level, width):
        self._signalNum = signalNum
        self._freq = freq
        self._count = count
        self._rate = rate
        self._level = level
        self._width = width

    def get_signal_number(self):
        return self._signalNum

    def get_description(self):
        desc = ('Freq: {:.3f}MHz\n'
                'Count: {} Rate: {:.2f}PPM\n'
                'Level: {:.3f} Width: {:.1f}ms')
        desc = desc.format(self._freq / 1e6,
                           self._count, self._rate,
                           self._level, self._width)

        return desc


# Basic timing
class Timing(object):
    _name = None
    _timings = {}

    def start(self, name):
        self._name = name
        if name not in self._timings:
            print name
            self._timings[name] = [0.] * 3

        self._timings[name][0] = time.clock()

    def stop(self):
        elapsed = time.clock() - self._timings[self._name][0]
        self._timings[self._name][1] += elapsed
        self._timings[self._name][2] += 1

    def print_timings(self):
        formatTimings = '\t{:<8} {:>4d} {:>8.3f}ms'
        print 'Timings:'
        print '\t{:<8} {:>4} {:>10}'.format('Routine', 'Runs', 'Average')
        for name, timing in self._timings.iteritems():
            if timing[2] != 0:
                print formatTimings.format(name,
                                           int(timing[2]),
                                           timing[1] * 1000. / timing[2])


# Print error and exit
def error(error):
    sys.exit(error)


# Parse command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(prog='demod_test.py',
                                     description='Demodulation test')

    parser.add_argument('-s', '--spectrum', help='Display capture spectrum',
                        action='store_true')
    parser.add_argument('-c', '--scan', help='Display signal scan',
                        action='store_true')
    parser.add_argument('-e', '--edges', help='Display pulse edges',
                        action='store_true')
    parser.add_argument('file', help='IQ wav file', nargs='?')
    args = parser.parse_args()

    if args.file is None:
        error('Please specify a file')
    if not os.path.isfile(args.file):
        error('Cannot find file')

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


# Get levels of each frequency
def analyse_frequencies(freqBins, magnitudes, frequencies):
    levels = []

    for freq in frequencies:
        # Closest bin
        fftBin = (numpy.abs(freqBins - freq)).argmin()
        level = magnitudes[fftBin]
        levels.append(level)

    return levels


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
        ax.plot(freqs + baseband, levels, linestyle='None', marker='o', color='r', label='Peaks')
        plt.legend(prop={'size': 10}, framealpha=0.8)

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
        levels = analyse_frequencies(freqBins, mags, frequencies)
        signals[chunkNum] = levels

        timing.stop()

    return signals


# Smooth signal
def smooth(signals, boxLen):
    box = numpy.ones(boxLen) / float(boxLen)

    for signalNum in range(signals.shape[0]):
        signals[signalNum] = numpy.convolve(signals[signalNum], box, mode='same')


# Find pulses and their frequency
def detect(baseband, frequencies, signals, showEdges):
    pulses = []

    length = signals.shape[1]
    # Calculate valid pulse widths with PULSE_WIDTH_TOL tolerance
    pulseWidths = [width * length / SAMPLE_TIME for width in sorted(PULSE_WIDTHS)]
    widthsMin = [width * (100 - PULSE_WIDTH_TOL) / 100. for width in pulseWidths]
    widthsMax = [width * (100 + PULSE_WIDTH_TOL) / 100. for width in pulseWidths]
    pulseWidths = zip(widthsMax, widthsMin)

    # Differentiate to find edges
    edges = numpy.empty((signals.shape[0], length - 1))
    for signalNum in range(signals.shape[0]):
        edges[signalNum] = numpy.diff(signals[signalNum])

    for signalNum in range(signals.shape[0]):
        timing.start('Detect')

        # Calculate thresholds based on percentiles
        signal = signals[signalNum]
        edge = edges[signalNum]
        t1 = numpy.percentile(edge[edge > 0], PULSE_THRESHOLD)
        t2 = numpy.mean(edge[edge > 0])
        t3 = numpy.percentile(edge[edge < 0], 100 - PULSE_THRESHOLD)
        t4 = numpy.mean(edge[edge < 0])
        threshPos = t2 + (t1 - t2) / 2
        threshNeg = t4 + (t3 - t4) / 2

        # Mark edges
        pos = edge > threshPos
        neg = edge < threshNeg
        # Find positive going edge indices
        posIndices = numpy.where((pos[1:] == False) & (pos[:-1] == True))[0]
        negIndices = numpy.where((neg[1:] == False) & (neg[:-1] == True))[0]
        minSize = min(len(posIndices), len(negIndices))
        posIndices = posIndices[:minSize]
        negIndices = negIndices[:minSize]
        # Find pulses of pulseWidths
        widthsFound = negIndices - posIndices
        for wMax, wMin in pulseWidths:
            valid = False
            widthsValid = widthsFound[(widthsFound > wMin) & (widthsFound < wMax)]
            # Must have at least 2 pulses
            if widthsValid.size > 1:
                pulseValid = posIndices[:widthsValid.size]
                # Calculate frequency
                pulseAvg = numpy.average(numpy.diff(pulseValid))
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
                    pulse = Pulse(signalNum,
                                  frequencies[signalNum] + baseband,
                                  widthsValid.size,
                                  freq * 60.,
                                  level,
                                  width * SAMPLE_TIME * 1000. / length)
                    pulses.append(pulse)
                    valid = True
                    break
        timing.stop()

        # Display differentiated signal with thresholds (-e)
        if showEdges:
            x = numpy.linspace(0, SAMPLE_TIME, edge.size)
            ax = plt.subplot(111)
            title = 'Signal Edges'
            if valid:
                title += ' (Pulse Found)'
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

    analysisLen = DEMOD_BINS / float(fs)
    print '\tDemod resolution (ms): {:.1f}'.format(analysisLen * 1000)

    print 'Analysis:'
    # Split input file into SAMPLE_TIME seconds blocks
    for blockNum in range(sampleBlocks):
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
        pulses = detect(baseband, frequencies, signals, args.edges)

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

