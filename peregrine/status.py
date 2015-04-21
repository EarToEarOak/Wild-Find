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
    STATUS = ['Idle', 'Waiting for fix', 'Capturing', 'Processing']

    _status = events.STATUS_IDLE
    _location = None
    _sats = []
    _log = []

    def __display(self):
        fix = '      --'
        lon = '        --'
        lat = '        --'
        if self._location is not None:
            lon = '{:10.5f}'.format(self._location[0][0])
            lat = '{:10.5f}'.format(self._location[0][1])
            fix = time.strftime('%H:%M:%S',
                                time.localtime(self._location[1]))
        desc = Status.STATUS[self._status - events.STATUS_IDLE]

        status = '\rStatus: {:15}  Lon: {:15}  Lat: {:15} Fix time: {:8}'
        status = status.format(desc, lon, lat, fix)
        sys.stdout.write(status)

    def set_status(self, status):
        self._status = status
        self.__display()

    def set_location(self, location):
        self._location = location
        self.__display()

    def set_sats(self, sats):
        self._sats = sats
        self.__display()

    def append_log(self, log):
        self._log.append(log)
        while len(log) > 24:
            del log[0]

    def get_location(self):
        return self._location
