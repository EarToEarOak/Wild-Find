import argparse
import os
import sys

import numpy
from scipy.io import wavfile

import matplotlib.pyplot as plt


# Sampling time per location (seconds)
SAMPLE_TIME = 3

# Size of each block to analyse
ANALYSIS_SIZE = 4096

# Collar frequencies (offsets from centre frequency)
# for use with SDRSharp_20141116_225753Z_152499kHz_IQ.wav
FREQUENCIES = [-167291,
               - 187153]


# Print error and exit
def error(error):
    sys.exit(error)


# Parse command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(prog='demod_test.py',
                                     description='Demodulation test')

    parser.add_argument('-s', '--spectrum', help='Show capture spectrum',
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
def analyse_frequencies(freqs, magnitudes):
    levels = []

    for freq in FREQUENCIES:
        fftBin = (numpy.abs(freqs - freq)).argmin()
        level = magnitudes[fftBin]
        levels.append(level)

    return levels


# Analyse block from capture
def analyse_block(fs, samples):
    chunks = samples.size / ANALYSIS_SIZE
    if chunks == 0:
        error('Sample time too long')

    signals = numpy.empty((chunks, len(FREQUENCIES)))

    # Split samples into chunks
    for i in range(chunks):
        chunkStart = i * ANALYSIS_SIZE
        chunk = samples[chunkStart:chunkStart + ANALYSIS_SIZE]

        # Analyse chunk
        fft = numpy.fft.fft(chunk) / ANALYSIS_SIZE
        mags = numpy.absolute(fft)
        freqs = numpy.fft.fftfreq(ANALYSIS_SIZE, 1. / fs)
        levels = analyse_frequencies(freqs, mags)
        signals[i] = levels

    return signals


# Main entry point
if __name__ == '__main__':
    args = parse_arguments()

    fs, iq = read_data(args.file)

    if args.spectrum:
        # Show spectrum of entire plot
        plt.psd(iq, NFFT=4096, Fs=fs)
        plt.show()

    sampleSize = fs * SAMPLE_TIME
    sampleBlocks = iq.size / sampleSize
    if sampleBlocks == 0:
        error('Capture too short')

    analysisLen = ANALYSIS_SIZE / float(fs)
    print 'Analysis length (ms): {:.1f}'.format(analysisLen * 1000)

    # Collar signals
    levels = []

    # Split input file into SAMPLE_TIME seconds blocks
    for i in range(sampleBlocks):
        sampleStart = i * sampleSize
        samples = iq[sampleStart:sampleStart + sampleSize]
        levels.append(analyse_block(fs, samples))

    # Plot each block
    for i in range(len(levels)):
        signals = levels[i]

        # Create the x axis time points
        startTime = i * SAMPLE_TIME
        x = numpy.linspace(startTime, startTime + SAMPLE_TIME, signals.shape[0])
        x = numpy.tile(x, (len(FREQUENCIES), 1)).T

        # Plot results
        plt.plot(x, signals)
        plt.title('Block {}'.format(i + 1))
        plt.xlabel('Time (s)')
        plt.ylabel('Level')
        plt.show()

