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
from PySide.QtCore import QModelIndex


class WidgetSignals(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        ui.loadUi(self, 'signals.ui')

        self._model = ModelSignals()
        self._tableSignals.setModel(self._model)
        self._tableSignals.resizeColumnsToContents()

        header = self._tableSignals.horizontalHeader()
        header.setResizeMode(QtGui.QHeaderView.Fixed)

        margins = self.layout().contentsMargins()
        width = self._tableSignals.verticalHeader().width()
        width += self._tableSignals.horizontalHeader().length()
        width += self._tableSignals.style().pixelMetric(QtGui.QStyle.PM_ScrollBarExtent)
        width += self._tableSignals.frameWidth() * 2
        width += margins.left() + margins.right()
        width += self.layout().spacing()
        self.setMaximumWidth(width)

    def set(self, frequencies):
        self._model.set(frequencies)
        self._tableSignals.setEnabled(True)

    def clear(self):
        self._model.set([])
        self._tableSignals.setEnabled(False)


class ModelSignals(QtCore.QAbstractTableModel):
    HEADER = ['Include', 'Frequency\n(MHz)', 'Detections']

    def __init__(self):
        QtCore.QAbstractTableModel.__init__(self)

        self._frequencies = []

    def rowCount(self, _parent):
        return len(self._frequencies)

    def columnCount(self, _parent):
        return len(self.HEADER)

    def headerData(self, col, orientation, role):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.HEADER[col]
        return None

    def data(self, index, role):
        value = self._frequencies[index.row()][index.column()]
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

#    def setData(self, index, value, role):
#        if role == QtCore.Qt.CheckStateRole:
#            self._frequencies[index.row()][index.column()] = value
#            return True
#
#        return False

#    def flags(self, index):
#        flags = (QtCore.Qt.ItemIsEnabled)
#        if index.column() == 0:
#            flags |= (QtCore.Qt.ItemIsEditable |
#                      QtCore.Qt.ItemIsUserCheckable)
#
#        return flags

    def set(self, frequencies):
        self.beginResetModel()
        del self._frequencies[:]
        for freq, count in frequencies:
            self._frequencies.append([QtCore.Qt.Checked, freq, count])
        self.endResetModel()


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
