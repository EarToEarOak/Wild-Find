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

from PySide import QtCore


class Model(QtCore.QAbstractTableModel):
    def __init__(self, signal, header, tips, formatters=None, selectable=None):
        QtCore.QAbstractTableModel.__init__(self)

        self._signal = signal
        self._header = header
        self._tips = tips
        self._formatters = formatters
        self._selectable = selectable
        self._data = []
        self._filtered = []

    def rowCount(self, _parent=None):
        return len(self._data)

    def columnCount(self, _parent):
        return len(self._header)

    def headerData(self, col, orientation, role):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self._header[col]
        elif role == QtCore.Qt.ToolTipRole:
            return self._tips[col]

        return None

    def data(self, index, role):
        value = self._data[index.row()][index.column()]
        data = None

        column = index.column()
        if role == QtCore.Qt.DisplayRole:
            if column != 0:
                data = self.__format(column, value)
        elif role == QtCore.Qt.CheckStateRole:
            if column == 0:
                data = value

        return data

    def setData(self, index, value, role):
        if role == QtCore.Qt.CheckStateRole:
            self._data[index.row()][index.column()] = value
            timeStamp = self._data[index.row()][1]
            checked = value == QtCore.Qt.Checked
            if checked:
                self._filtered.remove(timeStamp)
            else:
                self._filtered.append(timeStamp)

            self._signal.filter.emit()
            return True

        return False

    def flags(self, index):
        flags = QtCore.Qt.ItemIsEnabled
        column = index.column()
        if column == 0:
            flags |= (QtCore.Qt.ItemIsEditable |
                      QtCore.Qt.ItemIsUserCheckable)
        elif self._selectable is not None:
            if column == self._selectable:
                flags |= QtCore.Qt.ItemIsSelectable

        return flags

    def __format(self, column, value):
        if self._formatters is None:
            return value

        if self._formatters[column] is None:
            return value

        return self._formatters[column](value)

    def connect(self, slot):
        self._signal.filter.connect(slot)

    def set(self, data):
        self.beginResetModel()
        del self._data[:]
        for row in data:
            checked = QtCore.Qt.Checked
            if row[0] in self._filtered:
                checked = QtCore.Qt.Unchecked

            rowData = [checked]
            if not isinstance(row, list):
                rowData.extend([row])
            else:
                for column in row:
                    rowData.extend([column])
            self._data.append(rowData)

        self.endResetModel()

    def get(self):
        surveys = [data[1] for data in self._data]
        return surveys

    def get_all(self):
        return [data[1:] for data in self._data]

    def get_filtered(self):
        return self._filtered

    def set_filtered(self, filtered):
        self.beginResetModel()
        self._filtered = filtered
        for i in range(len(self._data)):
            data = self._data[i]
            if data[1] in filtered:
                data[0] = QtCore.Qt.Unchecked
            else:
                data[0] = QtCore.Qt.Checked

        self.endResetModel()

        self._signal.filter.emit()


def format_qtime(qDateTime):
    return QtCore.QDateTime().fromTime_t(qDateTime)


def format_freq(freq):
    return '{:8.4f}'.format(freq / 1e6)


def format_rate(rate):
    return '{:5.1f}'.format(rate)


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
