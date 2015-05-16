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

CW, AM = range(2)
MOD_DESC = ['CW', 'AM']


# Stores characteristics of detected collars
class Collar(object):
    # Index of the signal where it was found
    signalNum = None
    # Modulation type
    mod = None
    # Frequency (Hz)
    freq = None
    # Longitude
    lon = None
    # Latitude
    lat = None
    # Number of pulses
    count = None
    # Pulse rate (PPM)
    rate = None
    # Pulse level
    level = None
    # Pulse width
    width = None

    def __init__(self, count, rate, level, width):
        self.count = count
        self.rate = rate
        self.level = level
        self.width = width

    def get_description(self, baseband=0):
        desc = ('Freq: {:.3f}MHz Type: {}\n'
                'Count: {} Rate: {:.2f}PPM\n'
                'Level: {:.3f} Width: {:.1f}ms')
        desc = desc.format((self.freq + baseband) / 1e6,
                           MOD_DESC[self.mod],
                           self.count, self.rate,
                           self.level, self.width)

        return desc

    def get_dict(self, timeStamp):
        names = {'TimeStamp': timeStamp,
                 'Freq': self.freq,
                 'Mod': self.mod,
                 'Rate': self.rate,
                 'Level': self.level,
                 'Lon': self.lon,
                 'Lat': self.lat
                 }

        return names


if __name__ == '__main__':
    print 'Please run harrier.py'
    exit(1)
