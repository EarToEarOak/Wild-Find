#! /usr/bin/env python

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

import Queue
import argparse
import os
import signal
import socket
import sys
import time

from harrier import events
from harrier.constants import GPS_AGE, GPS_RETRY, SAMPLE_RATE
from harrier.database import Database
from harrier.gps import Gps
from harrier.receive import Receive
from harrier.server import Server
from harrier.settings import Settings
from harrier.status import Status
from harrier.testmode import TestMode
from harrier.utils import ArgparseFormatter


class Harrier(object):
    def __init__(self):
        settings = Settings(self.__arguments())
        self._settings = settings

        print 'Harrier\n'

        try:
            print 'Host :\t\t{} ({})'.format(socket.gethostname(),
                                             socket.gethostbyname(socket.getfqdn()))
        except socket.gaierror:
            pass

        queue = Queue.Queue()

        if settings.test:
            TestMode(settings)
            return

        print 'Survey:\t\t{}'.format(settings.survey)

        self._gps = None
        self._database = Database(settings.db, queue)
        self._receive = Receive(settings, queue)
        self._status = Status(self._database)
        self._server = Server(queue, self._status, self._database, settings)

        self._isScanning = False
        self._cancel = False
        self._signal = signal.signal(signal.SIGINT, self.__close)

        halfBand = SAMPLE_RATE / 2e6
        print 'Scan range:\t{:.2f}-{:.2f}MHz'.format(settings.freq - halfBand,
                                                     settings.freq + halfBand)

        if settings.delay is None:
            mode = 'Remote'
        else:
            mode = 'Automatic, after {}s'.format(settings.delay)
        print 'Scan mode:\t{}'.format(mode)

        events.Post(queue).gps_open(0)
        if settings.delay is not None:
            events.Post(queue).scan_start()

        while not self._cancel:
            if not queue.empty():
                self.__process_queue(settings, queue)
            else:
                try:
                    time.sleep(0.1)
                except IOError:
                    pass

        print '\nExiting...'
        waiting = self._status.get_wait()
        if waiting is not None:
            print '(Waiting for {} to finish)'.format(self._status.get_wait())

        self._cancel = True
        if self._server is not None:
            self._server.stop()
        if self._gps is not None:
            self._gps.stop()
        if self._receive is not None:
            self._receive.stop()
        if self._database is not None:
            self._database.stop()

    def __arguments(self):
        parser = argparse.ArgumentParser(description='Harrier',
                                         formatter_class=ArgparseFormatter)

        dirUser = os.path.expanduser('~')

        parser.add_argument('-f', '--frequency', help='Centre frequency (MHz)',
                            type=float, required=True)
        parser.add_argument('-g', '--gain', help='Gain (dB)',
                            type=float)
        parser.add_argument('-c', '--conf', help='Configuration file',
                            default=os.path.join(dirUser, 'harrier.conf'))

        groupNomal = parser.add_argument_group('Scan mode')
        groupNomal.add_argument('-s', '--survey', help='Survey name',
                                type=str,
                                default='Survey ' + time.strftime('%c'))
        groupNomal.add_argument('file', help='File', nargs='?',
                                default=os.path.join(dirUser, 'harrier.wfh'))

        groupTest = parser.add_argument_group('Test mode')
        groupTest.add_argument('-t', '--test', help='Test mode',
                               action='store_true')

        args = parser.parse_args()

        if not os.path.exists(args.conf):
            error = 'Configuration file {} not found\n'.format(args.conf)
            sys.stderr.write(error)
            parser.exit(1)

        return args

    def __process_queue(self, settings, queue):
        if self._cancel:
            return

        event = queue.get()
        eventType = event.get_type()

        # Start scan
        if eventType == events.SCAN_START:
            location = self._status.get_location()
            if location is None or time.time() - location[1] > GPS_AGE:
                self._status.set_status(events.STATUS_WAIT)
                events.Post(queue).scan_start(1)
            elif not self._isScanning:
                self._receive.receive()

            self._server.send_status()

        # Scan finished
        elif eventType == events.SCAN_DONE:
            self._isScanning = False
            timeStamp = event.get_arg('time')
            collars = event.get_arg('collars')
            if collars is not None:
                self._status.set_signals(len(collars))
                for collar in collars:
                    location = self._status.get_location()[0]
                    collar.lon = location[0]
                    collar.lat = location[1]
                    self._database.append_signal(timeStamp,
                                                 collar,
                                                 settings.freq,
                                                 self._settings.survey)
            else:
                self._status.set_signals(0)

            self._server.send_signals(timeStamp, collars)

            log = 'Found {} signals'.format(len(collars))
            logTime = self._database.append_log(log)
            self._server.send_log(logTime, log)

            if settings.delay is not None:
                events.Post(queue).scan_start(settings.delay)

            self._server.send_status()

        # Open GPS
        elif eventType == events.GPS_OPEN:
            if self._gps is None:
                print '\nStarting GPS'
                self._gps = Gps(settings.gps, queue)

        # GPS location
        elif eventType == events.GPS_LOC:
            self._status.set_location(event.get_arg('location'))
            self._server.send_status()

        # GPS satellites
        elif eventType == events.GPS_SATS:
            self._status.set_sats(event.get_arg('satellites'))
            self._server.send_sats()

        # GPS error
        elif eventType == events.GPS_ERR:
            self._gps = None
            error = '\nGPS error: {}'.format(event.get_arg('error'))
            print error
            print 'Retry in {}s'.format(GPS_RETRY)
            logTime = self._database.append_log(error)
            self._server.send_log(logTime, error)

            self._status.clear_gps()
            self._server.send_status()

            events.Post(queue).gps_open(GPS_RETRY)

        # Info
        elif eventType == events.INFO:
            self._status.clear_gps()
            info = '\nInfo: {}'.format(event.get_arg('info'))
            print info
            logTime = self._database.append_log(info)
            self._server.send_log(logTime, info)

        # Warning
        elif eventType == events.WARN:
            self._status.clear_gps()
            warning = '\nWarning: {}'.format(event.get_arg('warning'))
            print warning
            logTime = self._database.append_log(warning)
            self._server.send_log(logTime, log)

        # Error
        elif eventType == events.ERR:
            error = event.get_arg('error')
            sys.stderr.write(error)
            logTime = self._database.append_log(error)
            self._server.send_log(logTime, log)
            self.__close()
            exit(3)

        else:
            self._status.set_status(eventType)
            self._server.send_status()

    def __close(self, _signal=None, _frame=None):
        signal.signal(signal.SIGINT, self._signal)
        self._cancel = True


if __name__ == '__main__':
    try:
        Harrier()
    except KeyboardInterrupt:
        pass
