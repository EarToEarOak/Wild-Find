#!/usr/bin/env python

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


class Utils(object):
    # Print error and exit
    @staticmethod
    def error(error, fatal=True):
        if fatal:
            sys.exit(error)

        sys.stderr.write(error + '\n')

    # Return ranges based on tolerance
    @staticmethod
    def calc_tolerances(values, tolerance):
        valuesMin = [value * (100 - tolerance) / 100. for value in values]
        valuesMax = [value * (100 + tolerance) / 100. for value in values]
        return zip(valuesMax, valuesMin)


if __name__ == '__main__':
    print 'Please run harrier.py'
    exit(1)
