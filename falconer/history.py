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


import os

from PySide import QtGui, QtCore
from functools import partial


MAX_HISTORY = 5


class FileHistory(object):
    def __init__(self, menuBar, on_plotted):

        self._signal = FileHistorySignal()
        self._signal.open[str].connect(on_plotted)

        self._menuBar = menuBar
        self._history = []
        self._actions = []

    def __set_menu(self):
        menuRecent = self._menuBar.findChildren(QtGui.QMenu, '_menuRecent')[0]
        menuRecent.clear()

        self._actions = []
        for fileName in self._history:
            name = os.path.basename(fileName)
            action = QtGui.QAction(name, self._signal)
            action.setStatusTip(fileName)
            callback = partial(self._signal.open.emit, fileName)
            action.triggered.connect(callback)
            self._actions.append(action)
            menuRecent.addAction(action)

    def get(self):
        return self._history

    def set(self, history):
        self._history = history
        self.__set_menu()

    def add(self, fileName):
        if fileName in self._history:
            self._history.remove(fileName)
        self._history.insert(0, fileName)
        while len(self._history) > MAX_HISTORY:
            self._history.pop()

        self.__set_menu()


class FileHistorySignal(QtCore.QObject):
    open = QtCore.Signal(str)


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
