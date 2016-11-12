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

from PySide import QtGui

from common.constants import HARRIER_STATUS
from wildfind.falconer.utils_qt import set_max_text_width


class Status(object):

    READY, STARTING, LOADING, CREATING, OPENING, MERGING, SAVING, EXPORTING, \
        PRINTING, PROCESSING, CONNECTING, DOWNLOADING = range(12)

    _MESSAGES = ['Ready', 'Starting...', 'Loading...', 'Creating...',
                 'Opening...', 'Merging...', 'Saving...', 'Exporting...',
                 'Printing...', 'Processing...', 'Connecting to {}...',
                 'Downloading...']

    _CONNECTED = ['Not connected', 'Connected']
    _FIX = ['No fix', 'Fix']

    def __init__(self, statusBar):
        self._statusBar = statusBar

        statusBar.addPermanentWidget(QtGui.QLabel('Remote:'))

        self._labelConnected = QtGui.QLabel()
        self._labelConnected.setFrameStyle(QtGui.QFrame.Panel |
                                           QtGui.QFrame.Sunken)
        self._labelConnected.setToolTip('Remote connection')
        set_max_text_width(self._labelConnected, Status._CONNECTED)
        statusBar.addPermanentWidget(self._labelConnected)

        self._labelRemoteStatus = QtGui.QLabel()
        self._labelRemoteStatus.setFrameStyle(QtGui.QFrame.Panel |
                                              QtGui.QFrame.Sunken)
        self._labelRemoteStatus.setToolTip('Remote status')
        set_max_text_width(self._labelRemoteStatus, HARRIER_STATUS)
        statusBar.addPermanentWidget(self._labelRemoteStatus)

        self._labelRemoteFix = QtGui.QLabel()
        self._labelRemoteFix.setFrameStyle(QtGui.QFrame.Panel |
                                           QtGui.QFrame.Sunken)
        self._labelRemoteFix.setToolTip('Remote GPS fix')
        set_max_text_width(self._labelRemoteFix, Status._FIX)
        statusBar.addPermanentWidget(self._labelRemoteFix)

        self._labelRemoteSats = QtGui.QLabel()
        self._labelRemoteSats.setFrameStyle(QtGui.QFrame.Panel |
                                            QtGui.QFrame.Sunken)
        self._labelRemoteSats.setToolTip('Remote GPS satellites')
        set_max_text_width(self._labelRemoteSats, ['-- / --'])
        statusBar.addPermanentWidget(self._labelRemoteSats)

        self.set_remote_status({'status': 0,
                                'lon': None,
                                'lat': None})
        self.set_remote_sats(None)
        self.set_connected(False)

    def show_message(self, message, param=None):
        status = Status._MESSAGES[message]
        if param is not None:
            status = status.format(param)

        self._statusBar.showMessage(status)

    def set_connected(self, connected):
        self._labelConnected.setText(Status._CONNECTED[connected])
        if not connected:
            self._labelRemoteStatus.clear()
            self._labelRemoteFix.clear()
            self._labelRemoteSats.clear()

    def set_remote_status(self, remoteStatus):
        status = remoteStatus['status']
        lon = remoteStatus['lon']
        lat = remoteStatus['lat']
        fix = lon is not None and lat is not None

        self._labelRemoteStatus.setText(HARRIER_STATUS[status])
        self._labelRemoteFix.setText(Status._FIX[fix])

    def set_remote_sats(self, sats):
        if sats is None:
            self._labelRemoteSats.setText('--')
        else:
            if sats is not None and len(sats):
                total = len(sats[0])
                used = len([sat for _sat, sat in sats[0].iteritems()
                            if sat['Used']])
                self._labelRemoteSats.setText('{:2}/{:2}'.format(used, total))
            else:
                self._labelRemoteSats.setText('--')


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
