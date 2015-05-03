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
import signal
import sys
import time

from collar import MOD_DESC
import events
from receive import Receive


class TestMode(object):
    def __init__(self, settings):
        print 'Test mode'

        queue = Queue.Queue()

        self._receive = Receive(settings, queue)
        self._signal = signal.signal(signal.SIGINT, self.__close)

        events.Post(queue).scan_start()

        while self._receive.isAlive():
            if not queue.empty():
                self.__process_queue(settings, queue)

        self.__close()

    def __process_queue(self, settings, queue):
        event = queue.get()
        eventType = event.get_type()

        if eventType == events.SCAN_START:
            print 'Scanning...'
            self._receive.receive()

        elif eventType == events.SCAN_DONE:
            collars = event.get_arg('collars')
            if collars is not None:
                print 'Signals:'
                if len(collars):
                    for collar in collars:
                        collar.freq += settings.freq * 1e6
                        summary = '\t{:7.3f}MHz {:2} {:4.1f}PPM, {:4.1f}dB'
                        print summary.format(collar.freq / 1e6,
                                             MOD_DESC[collar.mod],
                                             collar.rate,
                                             collar.level)
                else:
                    print '\tNo signals found'
            events.Post(queue).scan_done()

        elif eventType == events.WARN:
            warning = 'Warning: {}'.format(event.get_arg('warning'))
            print warning

        elif eventType == events.ERR:
            error = event.get_arg('error')
            sys.stderr.write(error)
            self.__close()
            exit(3)

        time.sleep(0.05)

    def __close(self, _signal=None, _frame=None):
        signal.signal(signal.SIGINT, self._signal)
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
    print 'Please run peregrine.py'
    exit(1)