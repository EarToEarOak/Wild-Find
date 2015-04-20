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

import threading
import time


SCAN, SCAN_DONE, LOC, SATS, DB_SCANS, WARN, ERR = range(7)


class Event(object):
    def __init__(self, eventType, **kwargs):
        self._eventType = eventType
        self._args = kwargs

    def get_type(self):
        return self._eventType

    def get_arg(self, arg):
        if arg in self._args:
            return self._args[arg]

    def get_args(self):
        return self._args


class Post(object):
    def __init__(self, queue):
        self._queue = queue

    def __post(self, event, delay=0):
        if delay == 0:
            self._queue.put(event)
        else:
            thread = threading.Timer(delay, self._queue.put, args=(event,))
            thread.start()

    def scan(self, delay=0):
        event = Event(SCAN)
        self.__post(event, delay)

    def scan_done(self, collars=None, time=None):
        event = Event(SCAN_DONE, collars=collars, time=time)
        self.__post(event)

    def location(self, location):
        event = Event(LOC,
                      location=(location, time.time()))
        self.__post(event)

    def satellites(self, satellites):
        event = Event(SATS,
                      satellites=(satellites, time.time()))
        self.__post(event)

    def db_scans(self, scans):
        event = Event(DB_SCANS, scans=scans)
        self.__post(event)

    def error(self, error):
        event = Event(ERR, error=error)
        self.__post(event)

    def warning(self, warning):
        event = Event(WARN, warning=warning)
        self.__post(event)
