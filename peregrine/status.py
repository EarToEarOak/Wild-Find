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

import sys
import time

import events


LOG_SIZE = 25


class Status(object):
    STATUS = ['Idle', 'Locate', 'Capture', 'Process']

    _status = events.STATUS_IDLE
    _signals = 0
    _location = None
    _sats = []
    _log = []

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

    def append_log(self, log):
        self._log.append(log)
        while len(self._log) > 24:
            del self._log[0]

    def get_location(self):
        return self._location
