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
from falconer.utils_qt import TableSelectionMenu


class WidgetSignals(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        ui.loadUi(self, 'signals.ui')

        self._model = ModelSignals()
        proxyModel = QtGui.QSortFilterProxyModel(self)
        proxyModel.setDynamicSortFilter(True)
        proxyModel.setSourceModel(self._model)

        self._tableSignals.setModel(proxyModel)
        self._tableSignals.resizeColumnsToContents()
        self._contextMenu = TableSelectionMenu(self._tableSignals,
                                               self._model)

        header = self._tableSignals.horizontalHeader()
        header.setResizeMode(QtGui.QHeaderView.Fixed)

        self.__set_width()

    def __set_width(self):
        margins = self.layout().contentsMargins()
        width = self._tableSignals.verticalHeader().width()
        width += self._tableSignals.horizontalHeader().length()
        width += self._tableSignals.style().pixelMetric(QtGui.QStyle.PM_ScrollBarExtent)
        width += self._tableSignals.frameWidth() * 2
        width += margins.left() + margins.right()
        width += self.layout().spacing()
        self.setMaximumWidth(width)

    def connect(self, slot):
        self._model.connect(slot)

    def set(self, frequencies):
        self._model.set(frequencies)
        self._tableSignals.resizeColumnsToContents()
        self.__set_width()
        self._tableSignals.setEnabled(True)

    def get(self):
        return self._model.get()

    def get_filtered(self):
        return self._model.get_filtered()

    def clear(self):
        self._model.set([])
        self._tableSignals.setEnabled(False)


class ModelSignals(QtCore.QAbstractTableModel):
    HEADER = ['', 'Frequency\n(MHz)', 'Detections']

    def __init__(self):
        QtCore.QAbstractTableModel.__init__(self)

        self._signal = SignalSignals()
        self._signals = []
        self._filtered = []

    def rowCount(self, _parent):
        return len(self._signals)

    def columnCount(self, _parent):
        return len(self.HEADER)

    def headerData(self, col, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.HEADER[col]
        return None

    def data(self, index, role):
        value = self._signals[index.row()][index.column()]
        data = None

        if role == QtCore.Qt.DisplayRole:
            if index.column() == 1:
                data = '{:7.3f}'.format(value / 1e6)
            elif index.column() != 0:
                data = value
        elif role == QtCore.Qt.CheckStateRole:
            if index.column() == 0:
                data = value

        return data

    def setData(self, index, value, role):
        if role == QtCore.Qt.CheckStateRole:
            self._signals[index.row()][index.column()] = value
            frequency = self._signals[index.row()][1]
            checked = value == QtCore.Qt.Checked
            if checked:
                self._filtered.remove(frequency)
            else:
                self._filtered.append(frequency)

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

    def set(self, signals):
        self.beginResetModel()
        del self._signals[:]
        for frequency, count in signals:
            checked = QtCore.Qt.Checked
            if frequency in self._filtered:
                checked = QtCore.Qt.Unchecked
            self._signals.append([checked, frequency, count])
        self.endResetModel()

    def get(self):
        frequencies = []
        for checked, signal, _detects in self._signals:
            if checked == QtCore.Qt.Checked:
                frequencies.append(signal)

        return frequencies

    def get_filters(self):
        timeStamps = [timeStamp for _check, timeStamp, _freq in self._signals]
        return timeStamps

    def get_filtered(self):
        return self._filtered

    def set_filtered(self, filtered):
        self.beginResetModel()
        self._filtered = filtered
        for i in range(len(self._signals)):
            signal = self._signals[i]
            if signal[1] in filtered:
                signal[0] = QtCore.Qt.Unchecked
            else:
                signal[0] = QtCore.Qt.Checked

        self.endResetModel()
        self._signal.filter.emit()


class SignalSignals(QtCore.QObject):
    filter = QtCore.Signal()


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
