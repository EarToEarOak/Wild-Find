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


class WidgetScans(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        ui.loadUi(self, 'scans.ui')

        self._model = ModelScans()
        proxyModel = QtGui.QSortFilterProxyModel(self)
        proxyModel.setDynamicSortFilter(True)
        proxyModel.setSourceModel(self._model)

        self._tableScans.setModel(proxyModel)
        self._tableScans.resizeColumnsToContents()

        header = self._tableScans.horizontalHeader()
        header.setResizeMode(QtGui.QHeaderView.Fixed)

        self.__set_width()

    def __set_width(self):
        margins = self.layout().contentsMargins()
        width = self._tableScans.verticalHeader().width()
        width += self._tableScans.horizontalHeader().length()
        width += self._tableScans.style().pixelMetric(QtGui.QStyle.PM_ScrollBarExtent)
        width += self._tableScans.frameWidth() * 2
        width += margins.left() + margins.right()
        width += self.layout().spacing()
        self.setMaximumWidth(width)

    def connect(self, slot):
        self._model.connect(slot)

    def set(self, scans):
        self._model.set(scans)
        self._tableScans.resizeColumnsToContents()
        self.__set_width()
        self._tableScans.setEnabled(True)

    def get_filtered(self):
        return self._model.get_filtered()

    def clear(self):
        self._model.set([])
        self._model.clear_filtered()
        self._tableScans.setEnabled(False)


class ModelScans(QtCore.QAbstractTableModel):
    HEADER = ['', 'Time', 'Frequency\n(MHz)']

    def __init__(self):
        QtCore.QAbstractTableModel.__init__(self)

        self._signal = SignalScans()
        self._scans = []
        self._filtered = []

    def rowCount(self, _parent):
        return len(self._scans)

    def columnCount(self, _parent):
        return len(self.HEADER)

    def headerData(self, col, orientation, role):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.HEADER[col]
        return None

    def data(self, index, role):
        value = self._scans[index.row()][index.column()]
        data = None

        if role == QtCore.Qt.DisplayRole:
            if index.column() == 1:
                data = QtCore.QDateTime().fromTime_t(value)
            elif index.column() != 0:
                data = value
        elif role == QtCore.Qt.CheckStateRole:
            if index.column() == 0:
                data = value

        return data

    def setData(self, index, value, role):
        if role == QtCore.Qt.CheckStateRole:
            self._scans[index.row()][index.column()] = value
            timeStamp = self._scans[index.row()][1]
            checked = value == QtCore.Qt.Checked
            if checked:
                self._filtered.remove(timeStamp)
            else:
                self._filtered.append(timeStamp)

            self._signal.filter.emit()
            return True

        return False

    def flags(self, index):
        flags = (QtCore.Qt.ItemIsEnabled)
        if index.column() == 0:
            flags |= (QtCore.Qt.ItemIsEditable |
                      QtCore.Qt.ItemIsUserCheckable)

        return flags

    def connect(self, slot):
        self._signal.filter.connect(slot)

    def set(self, scans):
        self.beginResetModel()
        del self._scans[:]
        for timeStamp, count in scans:
            checked = QtCore.Qt.Checked
            if timeStamp in self._filtered:
                checked = QtCore.Qt.Unchecked
            self._scans.append([checked, timeStamp, count])
        self.endResetModel()

    def get_filtered(self):
        return self._filtered

    def clear_filtered(self):
        self._filtered = []


class SignalScans(QtCore.QObject):
    filter = QtCore.Signal()


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
