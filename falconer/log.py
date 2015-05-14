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

from PySide import QtGui, QtCore

from falconer import ui


class DialogLog(QtGui.QDialog):
    def __init__(self, parent, logs):
        QtGui.QDialog.__init__(self, parent)

        ui.loadUi(self, 'log.ui')

        self._model = ModelLog(logs)

        self._tableLog.setModel(self._model)
        self._tableLog.resizeColumnsToContents()

        header = self._tableLog.horizontalHeader()
        header.setResizeMode(QtGui.QHeaderView.Fixed)


class ModelLog(QtCore.QAbstractTableModel):
    HEADER = ['Time', 'Message']

    def __init__(self, logs):
        QtCore.QAbstractTableModel.__init__(self)

        self._logs = logs

    def rowCount(self, _parent):
        return len(self._logs)

    def columnCount(self, _parent):
        return len(self.HEADER)

    def headerData(self, col, orientation, role):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.HEADER[col]
        return None

    def data(self, index, role):
        value = self._logs[index.row()][index.column()]
        data = None

        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                data = QtCore.QDateTime().fromTime_t(value)
            else:
                data = value

        return data

    def flags(self, _index):
        flags = (QtCore.Qt.ItemIsEnabled)

        return flags

if __name__ == '__main__':
    print 'Please run falconer.py'
