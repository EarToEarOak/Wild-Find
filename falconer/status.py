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


class Status(object):

    READY, STARTING, LOADING, CREATING, OPENING, MERGING, SAVING, EXPORTING, \
        PRINTING, PROCESSING, CONNECTING, DOWNLOADING = range(12)

    _MESSAGES = ['Ready', 'Starting...', 'Loading...', 'Creating...',
                 'Opening...', 'Merging...', 'Saving...', 'Exporting...',
                 'Printing...', 'Processing...', 'Connecting to {}...',
                 'Downloading...']

    def __init__(self, statusBar):
        self._statusBar = statusBar

    def show_message(self, message, param=None):
        status = self._MESSAGES[message]
        if param is not None:
            status = status.format(param)

        self._statusBar.showMessage(status)


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
