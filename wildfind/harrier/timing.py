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

from collections import OrderedDict
import time


# Basic timing
class Timing(object):
    _name = None
    _timings = OrderedDict()
    _paused = None

    def start(self, name):
        self._name = name
        if name not in self._timings:
            self._timings[name] = [0.] * 3

        self._timings[name][0] = time.clock()

    def pause(self):
        self._paused = time.clock()

    def resume(self):
        elapsed = time.clock() - self._paused
        self._timings[self._name][0] += elapsed

    def stop(self):
        elapsed = time.clock() - self._timings[self._name][0]
        self._timings[self._name][1] += elapsed
        self._timings[self._name][2] += 1

    def print_timings(self):
        formatTimings = '\t{:<8} {:>6d} {:>10.3f} {:>13.3f}'
        print 'Timings:'
        print '\t{:<8} {:>6} {:>10} {:>12}'.format('Routine', 'Runs',
                                                   'Total (s)', 'Average (ms)')
        timeTotal = 0
        aveTotal = 0
        for name, timing in self._timings.iteritems():
            if timing[2] != 0:
                timeTotal += timing[1]
                ave = timing[1] * 1000. / timing[2]
                aveTotal += ave
                print formatTimings.format(name,
                                           int(timing[2]),
                                           timing[1],
                                           ave)

        print '\t{:<8} {:>17.3f} {:>13.3f}\n'.format('Total',
                                                     timeTotal,
                                                     aveTotal)


if __name__ == '__main__':
    print 'Please run harrier.py'
    exit(1)
