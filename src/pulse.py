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

    def get_description(self, baseband=0):
        desc = ('Freq: {:.3f}MHz Type: {}\n'
                'Count: {} Rate: {:.2f}PPM\n'
                'Level: {:.3f} Width: {:.1f}ms')
        desc = desc.format((self._freq+baseband) / 1e6,
                           self._mod,
                           self._count, self._rate,
                           self._level, self._width)

        return desc
