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

import Queue
import argparse
import os
import signal
import sys
from testmode import TestMode
import time

from constants import LOCATION_AGE
from database import Database
import events
from gps import Gps
from receive import Receive
from server import Server
from settings import Settings
from status import Status


class Peregrine(object):
    def __init__(self):
        print 'Peregrine'

        queue = Queue.Queue()

        settings = Settings(self.__arguments())

        if settings.test:
            TestMode(settings)
            return

        self._database = Database(settings.db, queue)
        self._receive = Receive(settings, queue)
        self._gps = Gps(settings.gps, queue)
        self._status = Status()
        self._server = Server(queue, self._status, self._database)

        self._isScanning = False
        self._isExiting = False
        self._signal = signal.signal(signal.SIGINT, self.__close)

        if settings.delay is not None:
            events.Post(queue).scan_done()

        while self._gps.isAlive():
            if not queue.empty():
                self.__process_queue(settings, queue)

        self.__close()

    def __arguments(self):
        parser = argparse.ArgumentParser(description=
                                         'Project Peregrine Receiver',
                                         formatter_class=
                                         argparse.ArgumentDefaultsHelpFormatter)

        parser.add_argument('-f', '--frequency', help='Centre frequency (MHz)',
                            type=float, required=True)
        parser.add_argument("-c", "--conf", help="Configuration file",
                            default=os.path.expanduser("~/peregrine.conf"))
        parser.add_argument("-t", "--test", help="Test mode",
                            action="store_true")
        parser.add_argument("file", help='Database path', nargs='?',
                            default=os.path.expanduser("~/peregrine.db"))

        args = parser.parse_args()

        if not os.path.exists(args.conf):
            error = 'Configuration file {} not found\n'.format(args.conf)
            sys.stderr.write(error)
            parser.exit(1)

        return args

    def __process_queue(self, settings, queue):
        if self._isExiting:
            return

        event = queue.get()
        eventType = event.get_type()

        # Start scan
        if eventType == events.SCAN:
            location = self._status.get_location()
            if location is None or time.time() - location[1] > LOCATION_AGE:
                self._status.set_status(events.STATUS_WAIT)
                events.Post(queue).scan(1)
            elif not self._isScanning:
                self._receive.receive()

        # Scan finished
        elif eventType == events.SCAN_DONE:
            self._isScanning = False
            timeStamp = event.get_arg('time')
            collars = event.get_arg('collars')
            if collars is not None:
                self._status.set_signals(len(collars))
                for collar in collars:
                    collar.freq += settings.freq * 1e6
                    location = self._status.get_location()[0]
                    collar.lon = location[0]
                    collar.lat = location[1]
                    self._database.append(timeStamp, collar)
            else:
                self._status.set_signals(0)
            if settings.delay is not None:
                events.Post(queue).scan(settings.delay)

        # Location
        elif eventType == events.LOC:
            self._status.set_location(event.get_arg('location'))

        # Satellites
        elif eventType == events.SATS:
            self._status.set_sats(event.get_arg('satellites'))

        # Warning
        elif eventType == events.WARN:
            warning = 'Warning: {}'.format(event.get_arg('warning'))
            print warning
            self._status.append_log(warning)

        # Error
        elif eventType == events.ERR:
            error = event.get_arg('error')
            sys.stderr.write(error)
            self._status.append_log(error)
            self.__close()
            exit(3)

        else:
            self._status.set_status(eventType)

        try:
            time.sleep(0.05)
        except IOError:
            pass

    def __close(self, _signal=None, _frame=None):
        signal.signal(signal.SIGINT, self._signal)
        self._isExiting = True
        print '\nExiting\n'
        if self._server is not None:
            self._server.close()
        if self._gps is not None:
            self._gps.stop()
        if self._receive is not None:
            self._receive.stop()
        if self._database is not None:
            self._database.stop()


if __name__ == '__main__':
    Peregrine()