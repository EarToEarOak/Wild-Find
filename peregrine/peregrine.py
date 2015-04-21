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
import sys
import time

from constants import LOCATION_AGE
from database import Database
import events
from gps import Gps
from receive import Receive
from settings import Settings
import status


class Peregrine(object):
    def __init__(self):
        queue = Queue.Queue()

        settings = Settings(self.__arguments())

        self._database = Database(settings.db, queue)
        self._receive = Receive(settings, queue)
        self._gps = Gps(settings.gps, queue)

        if settings.delay is not None:
            events.Post(queue).scan_done()

        while self._gps.isAlive():
            if not queue.empty():
                self.__process_queue(settings, queue)

        self.__close()
        print 'Exiting\n'

    def __arguments(self):
        parser = argparse.ArgumentParser(description=
                                         'Project Peregrine Receiver',
                                         formatter_class=
                                         argparse.ArgumentDefaultsHelpFormatter)

        parser.add_argument('-f', '--frequency', help='Centre frequency (MHz)',
                            type=float, required=True)
        parser.add_argument("-c", "--conf", help="Configuration file",
                            default=os.path.expanduser("~/peregrine.conf"))
        parser.add_argument("file", help='Database path', nargs='?',
                            default=os.path.expanduser("~/peregrine.db"))

        args = parser.parse_args()

        if not os.path.exists(args.conf):
            sys.stderr.write('Configuration file {} not found\n'.format(args.conf))
            parser.exit(1)

        if os.path.exists(args.file):
            print 'Appending data to {}'.format(args.file)
        else:
            print 'Creating {}'.format(args.file)

        return args

    def __process_queue(self, settings, queue):
        event = queue.get()
        eventType = event.get_type()

        # Start scan
        if eventType == events.SCAN:
            if status.location is None or time.time() - status.location[1] > LOCATION_AGE:
                status.receive = status.WAIT_LOC
                events.Post(queue).scan(1)
            elif self._receive is not None:
                status.receive = status.RUN
                self._receive.receive()

        # Scan finished
        elif eventType == events.SCAN_DONE:
            status.receive = status.IDLE
            timeStamp = event.get_arg('time')
            collars = event.get_arg('collars')
            if collars is not None:
                for collar in collars:
                    collar.freq += settings.freq * 1e6
                    collar.lon = status.location[0][0]
                    collar.lat = status.location[0][1]
                    self._database.append(timeStamp, collar)
            if settings.delay is not None:
                events.Post(queue).scan(settings.delay)

        # Location
        elif eventType == events.LOC:
            status.location = event.get_arg('location')
            self._database.get_scans()

        # Satellites
        elif eventType == events.SATS:
            status.sats = event.get_arg('satellites')

        # Warning
        elif eventType == events.WARN:
            warning = 'Warning: {}'.format(event.get_arg('warning'))
            print warning
            status.log_append(warning)

        # Error
        elif eventType == events.ERR:
            sys.stderr.write(event.get_arg('error'))
            self.__close()
            exit(3)

        else:
            time.sleep(0.05)

    def __close(self):
        self._gps.stop()
        self._receive.stop()
        self._database.stop()


if __name__ == '__main__':
    Peregrine()
