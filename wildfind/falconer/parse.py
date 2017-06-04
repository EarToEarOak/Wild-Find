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

import json

from PySide import QtCore


class Parse(object):
    def __init__(self, onOpened, onScans, onSignals, onLog,
                 onStatus, onSats, onSettings, onPorts, onShutdown):
        self._signal = SignalParse()
        self._signal.opened.connect(onOpened)
        self._signal.scans.connect(onScans)
        self._signal.signals.connect(onSignals)
        self._signal.log.connect(onLog)
        self._signal.status.connect(onStatus)
        self._signal.satellites.connect(onSats)
        self._signal.settings.connect(onSettings)
        self._signal.ports.connect(onPorts)
        self._signal.shutdown.connect(onShutdown)

        self._isConnected = False

    def __on_connect(self, result):
        if 'Application' in result:
            if result['Application'] == 'Harrier':
                self._isConnected = True
                self._signal.opened.emit()

    def __on_scans(self, result):
        scan = result['Value']
        if scan is not None:
            self._signal.scans.emit(scan)

    def __on_signals(self, result):
        scans = result['Value']
        if scans is not None:
            self._signal.signals.emit(scans)

    def __on_log(self, result):
        log = result['Value']
        if log is not None:
            self._signal.log.emit(log)

    def __on_status(self, result):
        log = result['Value']
        if log is not None:
            self._signal.status.emit(log)

    def __on_sats(self, result):
        sats = result['Value']
        if sats is not None:
            self._signal.satellites.emit(sats)

    def parse(self, data):
        try:
            result = json.loads(data)
        except ValueError:
            return

        if 'Method' in result:
            method = result['Method']
            if method == 'Connect':
                self.__on_connect(result)
            elif method == 'Scans':
                self.__on_scans(result)
            elif method == 'Signals':
                self.__on_signals(result)
            elif method == 'Log':
                self.__on_log(result)
            elif method == 'Status':
                self.__on_status(result)
            elif method == 'Satellites':
                self.__on_sats(result)
            elif method == 'Settings':
                self._signal.settings.emit(result)
            elif method == 'Ports':
                self._signal.ports.emit(result)
            elif method == 'Shutdown':
                self._signal.shutdown.emit()

    def is_connected(self):
        return self._isConnected

    def close(self):
        self._isConnected = False


class SignalParse(QtCore.QObject):
    opened = QtCore.Signal()
    scans = QtCore.Signal(dict)
    signals = QtCore.Signal(dict)
    log = QtCore.Signal(dict)
    status = QtCore.Signal(dict)
    satellites = QtCore.Signal(dict)
    settings = QtCore.Signal(dict)
    ports = QtCore.Signal(dict)
    shutdown = QtCore.Signal()

if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
