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

from wildfind.common.constants import HARRIER_PORT
from wildfind.falconer import ui
from wildfind.falconer.parse import Parse
from wildfind.falconer.status import Status
from wildfind.falconer.utils_qt import win_remove_context_help


TIMEOUT_CONNECT = 5


class Remote(object):
    def __init__(self, parent, status, database,
                 onOpened, onStatus, onSynched, onClosed):
        self._parent = parent
        self._status = status
        self._database = database

        self._client = None
        self._isDownloading = False
        self._record = False

        self._port = None
        self._delay = None
        self._freq = None
        self._ports = []

        self._timeout = QtCore.QTimer(parent)
        self._timeout.setSingleShot(True)
        self._timeout.timeout.connect(self.__on_timeout)

        self._parse = Parse(self.__on_opened,
                            self.__on_scans,
                            self.__on_signals,
                            self.__on_log,
                            onStatus,
                            self.__on_sats,
                            self.__on_settings,
                            self.__on_ports,
                            self.__on_shutdown)

        self._signal = SignalClient()
        self._signal.opened.connect(onOpened)
        self._signal.synched.connect(onSynched)
        self._signal.closed.connect(onClosed)
        self._signal.error.connect(self.__on_error)

    def __on_opened(self):
        self._timeout.stop()
        self._status.set_connected(True)
        message = 'Connection successful'
        QtGui.QMessageBox.information(self._parent,
                                      'Information',
                                      message)
        self._status.show_message(Status.READY)
        self._signal.opened.emit()

        self.__command('Get', 'Settings')
        self.__command('Get', 'Ports')

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
            self._status.show_message(Status.READY)
            QtGui.QMessageBox.information(self._parent,
                                          'Information',
                                          'Download finished')

        self._status.set_remote_log(log)

    def __on_sats(self, sats):
        self._status.set_remote_sats(sats)

    def __on_settings(self, settings):
        value = settings['Value']
        self._port = value['port']
        self._delay = value['delay']
        self._freq = value['frequency']

    def __on_ports(self, ports):
        self._ports = ports['Value']

    def __on_shutdown(self):
        QtGui.QMessageBox.warning(self._parent,
                                  'Warning',
                                  'Harrier has been shut down')
        self.close()

    def __on_timeout(self):
        self.close()
        self._status.show_message(Status.READY)
        QtGui.QMessageBox.critical(self._parent,
                                   'Error',
                                   'Connection failed')

    def __on_error(self, error):
        self.close()
        QtGui.QMessageBox.critical(self._parent, 'Remote error', error)
        self._status.show_message(Status.READY)

    def __command(self, command, method, value=None):
        resp = {}
        resp['Command'] = command
        resp['Method'] = method
        if value is not None:
            resp['Value'] = value
        self._client.send(json.dumps(resp) + '\r\n')

    def open(self, addr):
        if self._client is None:
            self._timeout.start(TIMEOUT_CONNECT * 1000)
            self._client = Client(addr, self._signal, self._parse)

    def download(self):
        self._isDownloading = True
        self._status.show_message(Status.DOWNLOADING)
        self.__command('Get', 'Scans')
        self.__command('Get', 'Signals')
        self.__command('Get', 'Log')

    def record(self, record):
        self._record = record

    def close(self):
        self._timeout.stop()
        if self._client is not None:
            self._client.close()
            self._client = None
        self._parse.close()
        self._status.set_connected(False)
        self._signal.closed.emit()

    def is_connected(self):
        return self._parse.is_connected()

    def get_settings(self):
        return self._port, self._delay, self._freq

    def get_ports(self):
        return self._ports

    def set_port(self, port):
        self.__command('Set', 'Port', port)
        self._port = port

    def set_frequency(self, freq):
        self.__command('Set', 'Frequency', freq)
        self._freq = freq

    def set_delay(self, delay):
        self.__command('Set', 'Delay', delay)
        self._delay = delay

    def scan(self):
        self.__command('Run', 'Scan')


class DialogRemoteConnect(QtGui.QDialog):
    def __init__(self, parent, settings):
        QtGui.QDialog.__init__(self, parent)

        self._settings = settings

        ui.loadUi(self, 'remote_connect.ui')
        win_remove_context_help(self)

        completer = QtGui.QCompleter(settings.remoteHistory, self)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self._editAddr.setCompleter(completer)

        self._editAddr.setText(settings.remoteAddr)

    @QtCore.Slot()
    def on__buttonBox_accepted(self):
        self._settings.remoteAddr = self._editAddr.text()
        self._settings.update_remote_history()
        self.accept()


class DialogRemoteSettings(QtGui.QDialog):
    def __init__(self, parent, remote):
        QtGui.QDialog.__init__(self, parent)

        self._remote = remote
        settings = remote.get_settings()
        ports = remote.get_ports()

        ui.loadUi(self, 'remote_settings.ui')
        win_remove_context_help(self)

        if settings[0] is not None:
            self._comboPort.addItems(ports)
            if settings[0] in ports:
                index = ports.index(settings[0])
                self._comboPort.setCurrentIndex(index)

        self._editFreq.setValidator(QtGui.QDoubleValidator(1, 9999, 1))
        self._editFreq.setText(str(settings[2]))

        self._editDelay.setValidator(QtGui.QDoubleValidator(0, 9999, 1))
        if settings[1] is not None:
            self._checkAuto.setChecked(True)
            self._editDelay.setEnabled(True)
            self._editDelay.setText(str(settings[1]))
        else:
            self._editDelay.setText('4')

    @QtCore.Slot(bool)
    def on__checkAuto_clicked(self, checked):
        self._editDelay.setEnabled(checked)

    @QtCore.Slot()
    def on__buttonBox_accepted(self):
        port = self._comboPort.currentText()
        freq = float(self._editFreq.text())
        auto = self._checkAuto.checkState()
        if auto:
            delay = float(self._editDelay.text())
        else:
            delay = None

        self._remote.set_port(port)
        self._remote.set_frequency(freq)
        self._remote.set_delay(delay)

        self.accept()


class Client(threading.Thread):
    def __init__(self, addr, signal, parse):
        threading.Thread.__init__(self)
        self.name = 'Client'

        self._addr = addr
        self._signal = signal
        self._parse = parse

        self._sock = None
        self._cancel = False

        self.start()

    def __read(self, sock):
        buf = ''
        data = True
        while data and not self._cancel:
            try:
                data = sock.recv(1024)
                if not data:
                    self.close()
            except socket.error:
                self.close()
            buf += data
            while buf.find('\n') != -1:
                line, buf = buf.split('\n', 1)
                yield line

    def run(self):
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.connect((self._addr, HARRIER_PORT))
        except socket.error as e:
            self._sock = None
            self._signal.error.emit(e.strerror)
            return

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
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except socket.error:
                pass
            self._sock.close()


class SignalClient(QtCore.QObject):
    opened = QtCore.Signal()
    synched = QtCore.Signal()
    closed = QtCore.Signal()
    error = QtCore.Signal(str)


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
