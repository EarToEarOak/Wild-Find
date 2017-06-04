#!/usr/bin/env python
#
#
# Wild Find
#
#
# Copyright 2014 - 2017 Al Brown
#
# Wildlife tracking and mapping
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import argparse
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


class ArgparseFormatter(argparse.HelpFormatter):
    def _get_help_string(self, action):
        help = action.help

        if action.required:
            help += ' (required)'

        if action.default is not None and '%(default)' not in action.help:
            if action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    help += ' (default: %(default)s)'

        return help


if __name__ == '__main__':
    print 'Please run harrier.py'
    exit(1)
