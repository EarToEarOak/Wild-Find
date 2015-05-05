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

from collections import OrderedDict
import sys
import time

from peregrine import events


class Status(object):
    STATUS = ['Idle', 'Locate', 'Capture', 'Process']

    _status = events.STATUS_IDLE
    _signals = 0
    _location = None
    _sats = []

    def __init__(self, database):
        self._database = database

    def __display(self):
        lon = '        --'
        lat = '        --'
        fix = '      --'
        if self._location is not None:
            lon = '{: 10.5f}'.format(self._location[0][0])
            lat = '{: 09.5f}'.format(self._location[0][1])
            fix = time.strftime('%H:%M:%S',
                                time.localtime(self._location[1]))
        desc = Status.STATUS[self._status - events.STATUS_IDLE]

        status = '\rStatus {:7}  Lon {:11}  Lat {:10}  Fix {:8}  Signals {:2}'
        status = status.format(desc, lon, lat, fix, self._signals)
        sys.stdout.write(status)

    def set_status(self, status):
        self._status = status
        self.__display()

    def set_signals(self, signals):
        self._signals = signals

    def set_location(self, location):
        self._location = location
        self.__display()

    def set_sats(self, sats):
        self._sats = sats
        self.__display()

    def clear_gps(self):
        self._location = None
        self._sats = []

    def get_location(self):
        return self._location

    def get_satellites(self):
        return self._sats

    def get(self):
        lon = None
        lat = None
        fix = None
        if self._location is not None:
            lon = self._location[0][0]
            lat = self._location[0][1]
            fix = self._location[1]

        size, space = self._database.get_size()

        resp = OrderedDict()
        resp['status'] = self._status - events.STATUS_IDLE
        resp['signals'] = self._signals
        resp['lon'] = lon
        resp['lat'] = lat
        resp['fix'] = fix
        resp['size'] = size
        resp['space'] = space

        return resp


if __name__ == '__main__':
    print 'Please run peregrine.py'
    exit(1)

