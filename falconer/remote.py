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

import json
import select
import socket
import threading

from PySide import QtCore, QtGui

from common.constants import PORT_HARRIER
from falconer.parse import Parse

TIMEOUT_CONNECT = 5


class Remote(object):
    def __init__(self, parent, statusbar, database, onOpened, onStatus, onSynched, onClosed):
        self._parent = parent
        self._statusbar = statusbar
        self._database = database

        self._client = None
        self._isDownloading = False
        self._record = False

        self._timeout = QtCore.QTimer(parent)
        self._timeout.setSingleShot(True)
        self._timeout.timeout.connect(self.__on_timeout)

        self._parse = Parse(self.__on_opened,
                            self.__on_scans,
                            self.__on_signals,
                            self.__on_log,
                            onStatus)

        self._signal = SignalClient()
        self._signal.opened.connect(onOpened)
        self._signal.synched.connect(onSynched)
        self._signal.closed.connect(onClosed)
        self._signal.error.connect(self.__on_error)

    def __on_opened(self):
        self._timeout.stop()
        message = 'Connection successful'
        QtGui.QMessageBox.information(self._parent,
                                      'Information',
                                      message)
        self._statusbar.showMessage('Ready')
        self._signal.opened.emit()

    def __on_scans(self, scans):
        if self._record or self._isDownloading:
            self._database.add_scans(scans)

    def __on_signals(self, signals):
        if self._record or self._isDownloading:
            self._database.add_signals(signals)
            self._signal.synched.emit()

    def __on_log(self, log):
        if self._record or self._isDownloading:
            self._database.add_log(log)

        if self._isDownloading:
            self._isDownloading = False
            self._statusbar.showMessage('Ready')
            QtGui.QMessageBox.information(self._parent,
                                          'Information',
                                          'Download finished')

    def __on_timeout(self):
        self.close()
        self._statusbar.showMessage('Ready')
        QtGui.QMessageBox.critical(self._parent,
                                   'Error',
                                   'Connection failed')

    def __on_error(self, error):
        self._timeout.stop()
        QtGui.QMessageBox.critical(self._parent, 'Remote error', error)
        self._statusbar.showMessage('Ready')

    def __command(self, command, method):
        resp = {}
        resp['Command'] = command
        resp['Method'] = method
        self._client.send(json.dumps(resp) + '\r\n')

    def open(self, addr):
        if self._client is None:
            self._timeout.start(TIMEOUT_CONNECT * 1000)
            self._client = Client(addr, self._signal, self._parse)

    def download(self):
        self._isDownloading = True
        self._statusbar.showMessage('Downloading...')
        self.__command('Get', 'Scans')
        self.__command('Get', 'Signals')
        self.__command('Get', 'Log')

    def record(self, record):
        self._record = record

    def close(self):
        if self._client is not None:
            self._client.close()
            self._client = None
        self._parse.close()
        self._signal.closed.emit()

    def is_connected(self):
        return self._parse.is_connected()


class Client(threading.Thread):
    def __init__(self, addr, signal, parse):
        threading.Thread.__init__(self)
        self.name = 'Client'

        self._signal = signal
        self._parse = parse

        self._sock = None
        self._cancel = False

        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.connect((addr, PORT_HARRIER))
        except socket.error as e:
            self._sock = None
            self._signal.error.emit(e.strerror)
            return

        self.start()

    def __read(self, sock):
        buf = ''
        data = True
        while data and not self._cancel:
            try:
                data = sock.recv(1024)
                if not data:
                    return
            except socket.error:
                return
            buf += data
            while buf.find('\n') != -1:
                line, buf = buf.split('\n', 1)
                yield line

    def run(self):
        while not self._cancel:
            read, _write, _error = select.select([self._sock], [], [], 0.5)

            for sock in read:
                for line in self.__read(sock):
                    self._parse.parse(line)

    def send(self, data):
        if self._sock is not None:
            self._sock.sendall(data)

    def close(self):
        self._cancel = True
        if self._sock is not None:
            self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()


class SignalClient(QtCore.QObject):
    opened = QtCore.Signal()
    synched = QtCore.Signal()
    closed = QtCore.Signal()
    error = QtCore.Signal(str)


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
