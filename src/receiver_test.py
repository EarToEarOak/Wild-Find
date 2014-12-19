import argparse
import os
import sys

import matplotlib
from matplotlib.widgets import RectangleSelector
import numpy
from scipy.io import wavfile

import matplotlib.pyplot as plt


# Sampling time per location (s)
SAMPLE_TIME = 3

# FFT bins used to scan
SCAN_BINS = 4096
# Size of each block to analyse
ANALYSIS_BINS = 4096

# Frequencies (offsets from centre frequency) (Hz)
# for use with SDRSharp_20141116_225753Z_152499kHz_IQ.wav
FREQUENCIES = [-167291,
               - 187153,
               - 209678]

# Pulse threshold (%)
PULSE_THRESHOLD = 99.5

# Pulse length (s)
PULSE_WIDTH = 25e-3
# Pulse width tolerance (+/i %)
PULSE_WIDTH_TOL = 20
# Valid pulse rates (ppm)
PULSE_RATES = [40, 60, 80]
# Pulse rate tolerance (+/- ppm)
PULSE_RATE_TOL = 10


# Print error and exit
def error(error):
    sys.exit(error)


# Parse command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(prog='demod_test.py',
                                     description='Demodulation test')

    parser.add_argument('-s', '--spectrum', help='Show capture spectrum',
                        action='store_true')
    parser.add_argument('-c', '--scan', help='Scan for signals',
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
    print 'Loading file: {}'.format(os.path.split(filename)[1])
    fs, data = wavfile.read(filename)

    if data.shape[1] != 2:
        error('Not an IQ file')
    if data.dtype != 'int16':
        error('Unexpected format')

    print 'Sample rate (MSPS): {:.2f}'.format(fs / 1e6)
    print 'Length (s): {:.2f}'.format(float(len(data)) / fs)

    # Scale data to +/-1
    data = data / 256.
    # Convert right/left to complex numbers
    iq = data[:, 1] + 1j * data[:, 0]

    return fs, iq


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
def scan(fs, samples):
    if samples.size < SCAN_BINS:
        error('Sample too short')

    # TODO: implement psd in Numpy rather than add another import
    l, f = matplotlib.mlab.psd(samples, SCAN_BINS, Fs=fs)
    peaks = (numpy.diff(numpy.sign(numpy.diff(l))) < 0).nonzero()[0] + 1
    freqs = f[peaks]

    # Plot results
    for freq in freqs:
        plt.axvline(freq, color='g', alpha=.5)

    decibels = 20 * numpy.log10(l)
    plt.plot(f, decibels)
    plt.title('Scan')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Level')
    plt.grid()
    plt.show()

    return freqs


# Analyse blocks from capture
def demod(fs, samples, frequencies):
    chunks = samples.size / ANALYSIS_BINS
    if chunks == 0:
        error('Sample time too long')

    signals = numpy.empty((chunks, len(frequencies)))

    # Split samples into chunks
    for i in range(chunks):
        chunkStart = i * ANALYSIS_BINS
        chunk = samples[chunkStart:chunkStart + ANALYSIS_BINS]

        # Analyse chunk
        fft = numpy.fft.fft(chunk) / ANALYSIS_BINS
        mags = numpy.absolute(fft)
        freqBins = numpy.fft.fftfreq(ANALYSIS_BINS, 1. / fs)
        levels = analyse_frequencies(freqBins, mags, frequencies)
        signals[i] = levels

    return signals


# Smooth signal
def smooth(signals, boxLen):
    box = numpy.ones(boxLen) / float(boxLen)

    for i in range(signals.shape[0]):
        signals[i] = numpy.convolve(signals[i], box, mode='same')


# Find pulses and their frequency
def measure_pulses(signals):
    pulses = []

    length = signals.shape[1]
    width = PULSE_WIDTH * length / SAMPLE_TIME
    # TODO: Improve tolerance levels
    widthMin = width * (100 - PULSE_WIDTH_TOL) / 100.
    widthMax = width * (100 + PULSE_WIDTH_TOL) / 100.

    # Differentiate to find edges
    edges = numpy.empty((signals.shape[0], length - 1))
    for i in range(signals.shape[0]):
        edges[i] = numpy.diff(signals[i])

    for i in range(signals.shape[0]):
        # TODO: find better thresholds
        signal = signals[i]
        edge = edges[i]
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
        iPos = numpy.where((pos[1:] == False) & (pos[:-1] == True))[0]
        iNeg = numpy.where((neg[1:] == False) & (neg[:-1] == True))[0]
        minSize = min(len(iPos), len(iNeg))
        iPos = iPos[:minSize]
        iNeg = iNeg[:minSize]
        # Find pulses of PULSE_WIDTH
        widths = iNeg - iPos
        widths = widths[(widths > widthMin) & (widths < widthMax)]
        # Must have at least 2 pulses
        if widths.size > 1:
            pulseValid = iPos[:widths.size]
            # Calculate frequency
            pulseAvg = numpy.average(numpy.diff(pulseValid))
            freq = length / (pulseAvg * float(SAMPLE_TIME))
            rate = freq * 60
            # Limit to PULSE_RATES
            closest = min(PULSE_RATES, key=lambda x: abs(x - rate))
            if (abs(closest - rate)) < PULSE_RATE_TOL:
                # Get pulse levels
                level = 0
                for j in range(len(pulseValid)):
                    pos = pulseValid[j]
                    width = widths[j]
                    pulse = signal[pos:pos + width - 1]
                    level += numpy.average(pulse)
                level /= len(pulseValid)
                pulses.append((widths.size, freq, level))
            else:
                pulses.append(None)
        else:
            pulses.append(None)

    return pulses


# Print width of dragged rectangle
def rectangle_callback(eclick, erelease):
    print 'Width {}'.format(abs(eclick.xdata - erelease.xdata))


# Main entry point
if __name__ == '__main__':
    args = parse_arguments()

    fs, iq = read_data(args.file)

    if args.spectrum:
        # Show spectrum of entire plot
        plt.psd(iq, NFFT=4096, Fs=fs)
        plt.title('Spectrum')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Level')
        plt.grid()
        plt.show()

    sampleSize = fs * SAMPLE_TIME
    sampleBlocks = iq.size / sampleSize
    if sampleBlocks == 0:
        error('Capture too short')

    analysisLen = ANALYSIS_BINS / float(fs)
    print 'Analysis length (ms): {:.1f}'.format(analysisLen * 1000)

    # Split input file into SAMPLE_TIME seconds blocks
    for i in range(sampleBlocks):
        sampleStart = i * sampleSize
        samples = iq[sampleStart:sampleStart + sampleSize]

        # Scan for possible signals
        if args.scan:
            frequencies = scan(fs, samples)
        else:
            frequencies = FREQUENCIES

        # Demodulate
        signals = demod(fs, samples, frequencies).T

        # Reduce noise
        smooth(signals, 4)
        # Find pulses
        pulses = measure_pulses(signals)

        # Plot results
        ax = plt.subplot(111)
        plt.title('Block {}'.format(i + 1))
        plt.xlabel('Time (s)')
        plt.ylabel('Level')
        plt.grid()

        # Create the x axis time points
        startTime = i * SAMPLE_TIME
        x = numpy.linspace(startTime, startTime + SAMPLE_TIME, signals.shape[1])

        for i in range(len(pulses)):
            if pulses[i] is not None:
                label = 'Freq: {:.3f}kHz, Count: {} Rate: {:.2f}Hz Level: {:.3f}'
                label = label.format(frequencies[i] / 1000., *pulses[i])
                plt.plot(x, signals[i], label=label)

        plt.legend(prop={'size': 10})

        # Add a rectangle selector of measurements
        selector = RectangleSelector(ax, rectangle_callback,
                                     drawtype='box', useblit=True)
        plt.show()
