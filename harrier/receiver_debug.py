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

import argparse
import ctypes
import os
import re
import sys
import time

import matplotlib
from matplotlib.patches import Rectangle
from matplotlib.ticker import EngFormatter
from matplotlib.widgets import RectangleSelector
import numpy
import rtlsdr
from scipy.io import wavfile

from harrier.constants import SAMPLE_TIME, SAMPLE_RATE, BLOCKS
from harrier.detect import Detect, DetectDebug, DEMOD_BINS, stream_to_complex
from harrier.scan import Scan, SCAN_BINS
from harrier.timing import Timing
from harrier.utils import Utils
import matplotlib.pyplot as plt


matplotlib.use('TkAgg')


class ReceiveDebug(object):
    def __init__(self, argList=None):
        self._args = self.__parse_arguments(argList)

        self._timing = Timing()

        self.debug = DetectDebug(self._args.edges, self._args.am,
                                 self._args.disableAm, self._args.verbose)
        callEdge = self.callback_egdes if self._args.edges is not None else None
        callAm = self.callback_am if self._args.am is not None else None
        self.debug.set_callbacks(callEdge, callAm)

        if 'wav' in self._args:
            self._source = SourceWav(self._args.wav, self._args.noise,
                                     self.__analyse)
        elif 'bin' in self._args:
            self._source = SourceBin(self._args.bin, self.__analyse)
        else:
            baseband = self._args.frequency * 1e6
            self._source = SourceRtlSdr(SAMPLE_RATE, baseband, self._args.gain,
                                        self.__analyse)

        if self._args.info:
            info = ('Info:\n'
                    '\tBlock size: {}s\n'
                    '\tScan resolution {:.2f}Hz\n'
                    '\tDemod resolution {:.2f}Hz ({:.2f}ms)\n')
            print (info).format(SAMPLE_TIME,
                                float(self._source.fs) / SCAN_BINS,
                                float(self._source.fs) / DEMOD_BINS,
                                DEMOD_BINS * 1e3 / float(self._source.fs))

        self._block = 0
        self._source.start(self._timing)

        print 'Done'

    # Parse command line arguments
    def __parse_arguments(self, argList=None):
        parser = argparse.ArgumentParser(description='Receiver testmode')

        parser.add_argument('-i', '--info', help='Display summary info',
                            action='store_true')
        parser.add_argument('-s', '--spectrum', help='Display capture spectrum',
                            action='store_true')
        parser.add_argument('-c', '--scan', help='Display signal search',
                            action='store_true')
        parser.add_argument('-e', '--edges', help='Display pulse edges',
                            type=float,
                            nargs='?', const=0, default=None)
        parser.add_argument('-a', '--am', help='Display AM detection',
                            action='store_true')
        parser.add_argument('-b', '--block', help='Block to process',
                            type=int, default=0)
        parser.add_argument('-da', '--disableAm', help='Disable AM detection',
                            action='store_true')
        parser.add_argument('--collars', help='Save capture if number of COLLARS not found',
                            type=int, default=None)
        parser.add_argument('-v', '--verbose', help='Be more verbose',
                            action='store_true')

        subparser = parser.add_subparsers(help='Source')

        parserWav = subparser.add_parser('wav')
        parserWav.add_argument('-n', '--noise', help='Add noise (dB)',
                               type=float, default=0)
        parserWav.add_argument('wav', help='IQ wav file')

        parserBin = subparser.add_parser('bin')
        parserBin.add_argument('bin', help='IQ bin file')

        parserRtl = subparser.add_parser('rtlsdr')
        parserRtl.add_argument('-f', '--frequency', help='RTLSDR frequency (MHz)',
                               type=float, required=True)
        parserRtl.add_argument('-g', '--gain', help='RTLSDR gain (dB)',
                               type=float, default=None)

        args = parser.parse_args(argList)

        if 'wav' in args and args.wav is not None and not os.path.isfile(args.wav):
            Utils.error('Cannot find wav file')

        if 'bin' in args and args.bin is not None and not os.path.isfile(args.bin):
            Utils.error('Cannot find bin file')

        if args.am and args.disableAm:
            Utils.error('AM detection disabled - will not display graphs', False)

        return args

    def __analyse(self, iq):
        print 'Analyse...'

        # Show spectrum of entire plot (-s)
        if self._args.spectrum:
            ax = plt.subplot(111)
            plt.psd(iq, NFFT=4096, Fs=self._source.fs)
            plt.title('Spectrum')
            plt.xlabel('Frequency (Hz)')
            plt.ylabel('Level')
            plt.grid()
            _selector = RectangleSelector(ax, self.__selection_freq,
                                          drawtype='box', useblit=True)
            plt.show()

        self._block += 1
        if self._args.block > 0 and self._args.block != self._block:
            return

        print 'Block {}'.format(self._block)

        if self._args.collars is not None:
            iq_copy = numpy.array(iq)

        scan = Scan(self._source.fs, iq, self._timing)
        frequencies = scan.search()
        if self._args.scan:
            # Show scan results
            freqs, levels = scan.get_spectrum()
            peaks = scan.get_peaks()
            _fig, ax = plt.subplots()
            ax.set_title('Scan')
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Level')
            ax.xaxis.set_major_formatter(EngFormatter(places=1))
            ax.fmt_xdata = EngFormatter(places=4, unit='Hz')
            ax.grid()

            ax.plot(freqs + self._source.baseband, levels, label='Signal')
            ax.plot(frequencies + self._source.baseband, peaks,
                    linestyle='None', marker='o',
                    color='r', label='Peaks')
            plt.legend(prop={'size': 10}, framealpha=0.8)
            # Add a rectangle selector for measurements
            _selector = RectangleSelector(ax, self.__selection_freq,
                                          drawtype='box', useblit=True)
            plt.show()

        print '\tSignals to demodulate: {}'.format(len(frequencies))
        if self._args.verbose:
            for freq in frequencies:
                print '\t\t{:.4f}MHz'.format((freq) / 1e6)

        # Detect
        detect = Detect(self._source.fs, iq, frequencies,
                        self._timing, self.debug)
        pulses = detect.search(self._source.baseband)
        signals = detect.get_signals()

        # Plot results
        ax = plt.subplot(111)
        plt.title('Block {}'.format(self._block))
        plt.xlabel('Time (s)')
        plt.ylabel('Level')
        plt.grid()

        self._timing.print_timings()
        print 'Found {} signals'.format(len(pulses))

        if self._args.collars is None:
            # Create the x axis time points
            startTime = self._block * SAMPLE_TIME
            if len(frequencies):
                x = numpy.linspace(startTime, startTime + SAMPLE_TIME,
                                   signals[0].shape[0])
            else:
                x = numpy.linspace(startTime, startTime + SAMPLE_TIME,
                                   1)

            # Plot the signals
            for pulse in pulses:
                signalNum = pulse.signalNum
                plt.plot(x, signals[signalNum],
                         label=pulse.get_description())

            if len(pulses):
                plt.legend(prop={'size': 10}, framealpha=0.5)

            # Add a rectangle selector for measurements
            _selector = RectangleSelector(ax, self.__selection_time,
                                          drawtype='box', useblit=True)
            plt.show()
        elif len(pulses) < self._args.collars:
            self.__save_iq(iq_copy)

    def __save_iq(self, iq):
        iq += 1 + 1j
        iq *= 255 / 2
        data = iq.view(numpy.float32)
        data = data.astype(numpy.uint8)

        print 'Saving "test.bin"'
        f = open('test.bin', 'wb')
        f.write(data)
        f.close()

        print 'Exiting'
        exit(1)

    # Display dragged rectangle
    def __selection_time(self, eventClick, eventRelease):
        xStart = eventClick.xdata
        xEnd = eventRelease.xdata
        yStart = eventClick.ydata
        yEnd = eventRelease.ydata
        width = xEnd - xStart
        height = yEnd - yStart

        axes = eventClick.inaxes

        self.__draw_selection(axes, xStart, yStart, width, height)

        dx = 'dT: {:.1f}ms'.format(abs(width) * 1000.)
        dy = 'dL: {:.4f}'.format(abs(height))
        text = 'Selection:\n\n' + dx + '\n' + dy
        self.__draw_text(axes, text)

    def __selection_freq(self, eventClick, eventRelease):
        xStart = eventClick.xdata
        xEnd = eventRelease.xdata
        yStart = eventClick.ydata
        yEnd = eventRelease.ydata
        width = xEnd - xStart
        height = yEnd - yStart

        axes = eventClick.inaxes

        self.__draw_selection(axes, xStart, yStart, width, height)

        dx = 'df: {:.1f}kHz'.format(abs(width) / 1000.)
        dy = 'dL: {:.4f}dB'.format(abs(height))
        text = 'Selection:\n\n' + dx + '\n' + dy
        self.__draw_text(axes, text)

    # Draw selection rectangle
    def __draw_selection(self, axes, x, y, width, height):
        self.__remove_child(axes, 'rectangeSelection')

        rectangle = Rectangle((x, y), width, height,
                              alpha=0.5,
                              facecolor='grey',
                              edgecolor='black',
                              gid='rectangeSelection')
        axes.add_patch(rectangle)

    # Draw text in upper right
    def __draw_text(self, axes, text):
        self.__remove_child(axes, 'boxText')

        bbox = dict(alpha=0.8, facecolor='w')
        plt.text(0.02, 0.98, text, size=10,
                 transform=axes.transAxes,
                 verticalalignment='top',
                 bbox=bbox,
                 gid='boxText')
        plt.draw()

    # Remove child from plot
    def __remove_child(self, axes, gid):
        for child in axes.get_children():
            if child.get_gid() is not None:
                if child.get_gid() is gid:
                    child.remove()

    # Callback to display edge plot
    def callback_egdes(self, baseband, edge, signalNum, pulse, frequencies,
                       threshPos, threshNeg, posIndices, negIndices):

        freq = frequencies[signalNum] + baseband
        edges = self._args.edges * 1e6
        if edges != 0 and (abs(freq - edges) > 50e3):
            return

        x = numpy.linspace(0, SAMPLE_TIME, edge.size)
        ax = plt.subplot(111)
        title = 'Signal Edges ({})'.format(signalNum + 1)
        if pulse is not None:
            title += ' (Pulses Found - {})'.format(pulse.get_modulation())
        plt.title(title)
        plt.grid()
        label = '{:.4f}MHz'.format(freq / 1e6)
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
        _selector = RectangleSelector(ax, self.__selection_time,
                                      drawtype='box', useblit=True)
        plt.show()

    # Callback to display AM plot
    def callback_am(self, signal, am, freq, amPosIndices, amNegIndices):
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
        _selector = RectangleSelector(ax, self.__selection_time,
                                      drawtype='box', useblit=True)
        plt.show()


# Wav file source
class SourceWav(object):
    def __init__(self, filename, noiseLevel, callback):
        self._callback = callback

        name = os.path.split(filename)[1]

        print 'Wav file:'
        print '\tLoading capture file: {}'.format(name)
        self.fs, data = wavfile.read(filename)

        if data.shape[1] != 2:
            Utils.error('Not an IQ file')
        if data.dtype not in ['int16', 'uint16', 'int8', 'uint8']:
            Utils.error('Unexpected format')

        # Get baseband from filename
        regex = re.compile(r'_(\d+)kHz_IQ')
        matches = regex.search(name)
        if matches is not None:
            self.baseband = int(matches.group(1)) * 1000
        else:
            self.baseband = 0

        print '\tSample rate: {:.2f}MSPS'.format(self.fs / 1e6)
        print '\tLength: {:.2f}s'.format(float(len(data)) / self.fs)

        # Scale data to +/-1
        data = data.astype(numpy.float32, copy=False)
        data /= 256.
        # Convert right/left to complex numbers
        self.iq = 1j * data[..., 0]
        self.iq += data[..., 1]

        # Add noise
        if noiseLevel > 0:
            noiseI = numpy.random.uniform(-1, 1, self.iq.size)
            noiseQ = numpy.random.uniform(-1, 1, self.iq.size)

            self.iq += (noiseI + 1j * noiseQ) * 10. ** (noiseLevel / 10.)

    # Return wav file samples
    def start(self, _timing=None):
        sampleSize = self.fs * SAMPLE_TIME
        sampleBlocks = self.iq.size / sampleSize
        if sampleBlocks == 0:
            Utils.error('Capture too short')

        for blockNum in range(sampleBlocks):
            sampleStart = blockNum * sampleSize
            samples = self.iq[sampleStart:sampleStart + sampleSize]

            self._callback(samples)


# Bin file source
class SourceBin(object):
    def __init__(self, filename, callback):
        self._filename = filename
        self._callback = callback
        self.fs = 2.4e6
        self.baseband = 0

        name = os.path.split(filename)[1]

        print 'Bin file:'
        print '\tLoading capture file: {}'.format(name)

        print '\tSample rate: {:.2f}MSPS (assumed)'.format(self.fs / 1e6)
        length = os.path.getsize(filename)
        print '\tLength: {:.2f}s'.format(length / (self.fs * 2.))

    # Return bin file samples
    def start(self, _timing=None):
        length = os.path.getsize(self._filename) / 2
        sampleSize = int(self.fs * SAMPLE_TIME)
        sampleBlocks = int(length / sampleSize)
        if sampleBlocks == 0:
            Utils.error('Capture too short')

        f = open(self._filename, 'rb')

        for _i in range(sampleBlocks):
            data = bytearray(f.read(sampleSize * 2))
            iq = numpy.array(data).astype(numpy.float32).view(numpy.complex64)
            iq /= 255.

            self._callback(iq)

        f.close()


# RTLSDR Source
class SourceRtlSdr(object):
    def __init__(self, fs, baseband, gain, callback):
        self._gain = gain
        self.fs = fs
        self.baseband = baseband
        self._callback = callback

        self._capture = (ctypes.c_ubyte * int(2 * SAMPLE_RATE * SAMPLE_TIME))()
        self._captureBlock = 0

        print 'RTLSDR:'
        print '\tSample rate: {:.2f}MSPS'.format(fs / 1e6)
        print '\tFrequency: {:.2f}MHz'.format(baseband / 1e6)

        self._sdr = rtlsdr.RtlSdr()
        self._sdr.set_sample_rate(self.fs)
        if self._gain is not None:
            self._sdr.set_gain(self._gain)
            gain = self._sdr.get_gain()
            print '\tGain: {:.1f}dB'.format(gain)
        self._sdr.set_center_freq(self.baseband)
        time.sleep(1)

    def __capture(self, data, _sdr):
        length = len(data)
        pos = self._captureBlock * length
        dst = ctypes.byref(self._capture, pos)
        ctypes.memmove(dst, data, length * ctypes.sizeof(ctypes.c_ubyte))

        self._captureBlock += 1
        progress = 100.*self._captureBlock / BLOCKS
        sys.stdout.write('{:.0f}%\r'.format(progress))
        sys.stdout.flush()

        if self._captureBlock == BLOCKS:
            self._sdr.cancel_read_async()
            self._captureBlock = 0

    def start(self, timing):
        while True:
            print 'Capturing...'
            self._sdr.read_bytes_async(self.__capture,
                                       2 * SAMPLE_RATE * SAMPLE_TIME / BLOCKS)
            timing.start('Convert')
            iq = stream_to_complex(self._capture)
            timing.stop()
            self._callback(iq)


def main(argList=None):
    ReceiveDebug(argList)

# Main entry point
if __name__ == '__main__':
    main()
