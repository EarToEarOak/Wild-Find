#! /usr/bin/env python

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

import argparse
import os
import re

import matplotlib
from matplotlib.patches import Rectangle
from matplotlib.ticker import EngFormatter
from matplotlib.widgets import RectangleSelector
import numpy
from scipy.io import wavfile

from constants import SAMPLE_TIME, SAMPLE_RATE
from detect import Detect, DetectDebug
import matplotlib.pyplot as plt
from scan import Scan
from timing import Timing
from utils import Utils


matplotlib.use('TkAgg')


# Parse command line arguments
def parse_arguments(argList=None):
    parser = argparse.ArgumentParser(description='Receiver testmode')

    parser.add_argument('-i', '--info', help='Display summary info',
                        action='store_true')
    parser.add_argument('-s', '--spectrum', help='Display capture spectrum',
                        action='store_true')
    parser.add_argument('-c', '--scan', help='Display signal search',
                        action='store_true')
    parser.add_argument('-e', '--edges', help='Display pulse edges',
                        action='store_true')
    parser.add_argument('-a', '--am', help='Display AM detection',
                        action='store_true')
    parser.add_argument('-b', '--block', help='Block to process',
                        type=int, default=0)
    parser.add_argument('-da', '--disableAm', help='Disable AM detection',
                        action='store_true')
    parser.add_argument('-v', '--verbose', help='Be more verbose',
                        action='store_true')

    subparser = parser.add_subparsers(help='Source')

    parserWav = subparser.add_parser('wav')
    parserWav.add_argument('-n', '--noise', help='Add noise (dB)',
                           type=float, default=0)
    parserWav.add_argument('wav', help='IQ wav file')

    parserRtl = subparser.add_parser('rtlsdr')
    parserRtl.add_argument('-f', '--frequency', help='RTLSDR frequency (MHz)',
                           type=float, required=True)
    parserRtl.add_argument('-g', '--gain', help='RTLSDR gain (dB)',
                           type=float, default=None)

    args = parser.parse_args(argList)

    if 'wav' in args and args.wav is not None and not os.path.isfile(args.wav):
        Utils.error('Cannot find file')

    if args.am and args.disableAm:
        Utils.error('AM detection disabled - will not display graphs', False)

    return args


# Read data from wav file
def read_wav(filename, noiseLevel):
    name = os.path.split(filename)[1]

    print 'Wav file:'
    print '\tLoading capture file: {}'.format(name)
    fs, data = wavfile.read(filename)

    if data.shape[1] != 2:
        Utils.error('Not an IQ file')
    if data.dtype != 'int16':
        Utils.error('Unexpected format')

    # Get baseband from filename
    regex = re.compile(r'_(\d+)kHz_IQ')
    matches = regex.search(name)
    if matches is not None:
        baseband = int(matches.group(1)) * 1000
    else:
        baseband = 0

    print '\tSample rate: {:.2f}MSPS'.format(fs / 1e6)
    print '\tLength: {:.2f}s'.format(float(len(data)) / fs)

    # Scale data to +/-1
    data = data / 256.
    # Convert right/left to complex numbers
    iq = data[:, 1] + 1j * data[:, 0]

    # Add noise
    if noiseLevel > 0:
        noiseI = numpy.random.uniform(-1, 1, iq.size)
        noiseQ = numpy.random.uniform(-1, 1, iq.size)

        iq += (noiseI + 1j * noiseQ) * 10. ** (noiseLevel / 10.)

    return baseband, fs, iq


# Return wav file samples
def source_wav(fs, iq):
    sampleSize = fs * SAMPLE_TIME
    sampleBlocks = iq.size / sampleSize
    if sampleBlocks == 0:
        Utils.error('Capture too short')

    for blockNum in range(sampleBlocks):
        sampleStart = blockNum * sampleSize
        samples = iq[sampleStart:sampleStart + sampleSize]

        yield samples


# Return rtlsdr samples
def source_sdr(sdr, timing):
    samples = SAMPLE_RATE * SAMPLE_TIME
    while True:
        print 'Capturing...'
        timing.start('Radio')
        capture = sdr.read_samples(samples)
        timing.stop()
        yield capture


# Callback to display edge plot
def callback_egdes(edge, signalNum, pulse, frequencies,
                   threshPos, threshNeg, posIndices, negIndices):
    x = numpy.linspace(0, SAMPLE_TIME, edge.size)
    ax = plt.subplot(111)
    title = 'Signal Edges ({})'.format(signalNum + 1)
    if pulse is not None:
        title += ' (Pulses Found - {})'.format(pulse.mod)
    plt.title(title)
    plt.grid()
    label = '{:.3f}MHz'.format((frequencies[signalNum]) / 1e6)
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


# Callback to display AM plot
def callback_am(signal, am, freq, amPosIndices, amNegIndices):
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


def main(argList=None):
    args = parse_arguments(argList)

    timing = Timing()

    debug = DetectDebug(args.edges, args.am, args.disableAm, args.verbose)
    callEdge = callback_egdes if args.edges else None
    callAm = callback_am if args.am else None
    debug.set_callbacks(callEdge, callAm)

    if 'wav' in args:
        # Read source file
        baseband, fs, iq = read_wav(args.wav, args.noise)
        source = source_wav(fs, iq)
    else:
        import rtlsdr
        baseband = args.frequency * 1e6
        fs = SAMPLE_RATE
        print 'RTLSDR:'
        print '\tSample rate: {:.2f}MSPS'.format(fs / 1e6)
        print '\tFrequency: {:.2f}MHz'.format(baseband / 1e6)
        sdr = rtlsdr.RtlSdr()
        sdr.set_sample_rate(fs)
        if args.gain is not None:
            sdr.set_gain(args.gain)
            print '\tGain: {:.1f}dB'.format(args.gain)
        sdr.set_center_freq(baseband)
        source = source_sdr(sdr, timing)

    if args.info:
        info = ('Info:\n'
                '\tBlock size: {}s\n'
                '\tScan resolution {:.2f}Hz\n'
                '\tDemod resolution {:.2f}Hz ({:.2f}ms)\n')
        print (info).format(SAMPLE_TIME,
                            float(fs) / Scan.SCAN_BINS,
                            float(fs) / Detect.DEMOD_BINS,
                            Detect.DEMOD_BINS * 1e3 / float(fs))

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

    # Analyse capture
    blockNum = 0
    for samples in source:
        if args.block > 0 and args.block != blockNum + 1:
            continue

        print 'Block {}'.format(blockNum + 1)

        scan = Scan(fs, samples, timing)
        frequencies = scan.search()
        if args.scan:
            # Show scan results
            freqs, levels = scan.get_spectrum()
            peaks = scan.get_peaks()
            _fig, ax = plt.subplots()
            ax.set_title('Scan')
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Level')
            ax.xaxis.set_major_formatter(EngFormatter(places=1))
            ax.grid()

            ax.plot(freqs + baseband, levels, label='Signal')
            ax.plot(frequencies + baseband, peaks,
                    linestyle='None', marker='o',
                    color='r', label='Peaks')
            plt.legend(prop={'size': 10}, framealpha=0.8)
            # Add a rectangle selector for measurements
            _selector = RectangleSelector(ax, selection_freq,
                                          drawtype='box', useblit=True)
            plt.show()

        print '\tSignals to demodulate: {}'.format(len(frequencies))
        if args.verbose:
            for freq in frequencies:
                print '\t\t{:.3f}MHz'.format((baseband + freq) / 1e6)

        # Detect
        detect = Detect(fs, samples, frequencies, timing, debug)
        pulses = detect.search()
        signals = detect.get_signals()

        # Plot results
        ax = plt.subplot(111)
        plt.title('Block {}'.format(blockNum + 1))
        plt.xlabel('Time (s)')
        plt.ylabel('Level')
        plt.grid()

        # Create the x axis time points
        startTime = blockNum * SAMPLE_TIME
        x = numpy.linspace(startTime, startTime + SAMPLE_TIME,
                           signals[0].shape[0])

        timing.print_timings()

        # Plot the signals
        for pulse in pulses:
            signalNum = pulse.signalNum
            plt.plot(x, signals[signalNum],
                     label=pulse.get_description(baseband))

        if len(pulses):
            plt.legend(prop={'size': 10}, framealpha=0.5)

        # Add a rectangle selector for measurements
        _selector = RectangleSelector(ax, selection_time,
                                      drawtype='box', useblit=True)
        plt.show()
        blockNum += 1

    print 'Done'

# Main entry point
if __name__ == '__main__':
    main()
