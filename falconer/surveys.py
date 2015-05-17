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


from PySide import QtGui, QtCore

from falconer import ui
from falconer.utils_qt import TableSelectionMenu


class WidgetSurveys(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self._signal = SignalSurveys()

        ui.loadUi(self, 'surveys.ui')

        self._model = ModelSurveys(self)
        proxyModel = QtGui.QSortFilterProxyModel(self)
        proxyModel.setDynamicSortFilter(True)
        proxyModel.setSourceModel(self._model)

        self._tableSurveys.setModel(proxyModel)
        self._tableSurveys.resizeColumnsToContents()
        self._contextMenu = TableSelectionMenu(self._tableSurveys,
                                               self._model)

        header = self._tableSurveys.horizontalHeader()
        header.setResizeMode(QtGui.QHeaderView.Fixed)

        self.__set_width()

    def __set_width(self):
        margins = self.layout().contentsMargins()
        width = self._tableSurveys.verticalHeader().width()
        width += self._tableSurveys.horizontalHeader().length()
        width += self._tableSurveys.style().pixelMetric(QtGui.QStyle.PM_ScrollBarExtent)
        width += self._tableSurveys.frameWidth() * 2
        width += margins.left() + margins.right()
        width += self.layout().spacing()
        self.setMaximumWidth(width)

    @QtCore.Slot(str)
    def on__comboSurveys_activated(self, survey):
        if survey == 'All':
            self._model.set_filtered([])
        else:
            surveys = self._model.get()
            surveys.remove(survey.encode("utf-8"))
            self._model.set_filtered(surveys)

    def on_filter(self):
        surveys = self._model.get()
        filtered = self._model.get_filtered()
        selected = set(surveys) - set(filtered)
        if len(filtered) == 0:
            self._comboSurveys.setCurrentIndex(0)
        elif len(selected) == 1:
            index = surveys.index(list(selected)[0])
            self._comboSurveys.setCurrentIndex(index + 1)
        else:
            self._comboSurveys.setCurrentIndex(-1)

        self._signal.filter.emit()

    @QtCore.Slot()
    def connect(self, slot):
        self._signal.filter.connect(slot)

    def set(self, surveys):
        self._model.set(surveys)
        self._tableSurveys.resizeColumnsToContents()
        self.__set_width()

        for i in range(self._comboSurveys.count()):
            self._comboSurveys.removeItem(i)

        self._comboSurveys.addItem('All')
        self._comboSurveys.addItems(surveys)

        self._tableSurveys.setEnabled(True)
        self._comboSurveys.setEnabled(True)

    def get(self):
        return self._model.get()

    def get_filtered(self):
        return self._model.get_filtered()

    def clear(self):
        self._model.set([])
        self._model.set_filtered([])
        self._tableSurveys.setEnabled(False)
        self._comboSurveys.setEnabled(False)


class ModelSurveys(QtCore.QAbstractTableModel):
    HEADER = [None, 'Name']

    def __init__(self, parent):
        QtCore.QAbstractTableModel.__init__(self)

        self._signal = SignalSurveys()
        self._signal.filter.connect(parent.on_filter)
        self._surveys = []
        self._filtered = []

    def rowCount(self, _parent):
        return len(self._surveys)

    def columnCount(self, _parent):
        return len(self.HEADER)

    def headerData(self, col, orientation, role):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.HEADER[col]
        return None

    def data(self, index, role):
        value = self._surveys[index.row()][index.column()]
        data = None

        if role == QtCore.Qt.DisplayRole:
            if index.column() == 1:
                data = value
            elif index.column() != 0:
                data = value
        elif role == QtCore.Qt.CheckStateRole:
            if index.column() == 0:
                data = value

        return data

    def setData(self, index, value, role):
        if role == QtCore.Qt.CheckStateRole:
            self._surveys[index.row()][index.column()] = value
            timeStamp = self._surveys[index.row()][1]
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

    def set(self, surveys):
        self.beginResetModel()
        del self._surveys[:]
        for name in surveys:
            checked = QtCore.Qt.Checked
            if name in self._filtered:
                checked = QtCore.Qt.Unchecked
            self._surveys.append([checked, name])
        self.endResetModel()

    def get(self):
        surveys = [survey for _check, survey in self._surveys]
        return surveys

    def get_filtered(self):
        return self._filtered

    def set_filtered(self, filtered):
        self.beginResetModel()
        self._filtered = filtered
        for i in range(len(self._surveys)):
            survey = self._surveys[i]
            if survey[1] in filtered:
                survey[0] = QtCore.Qt.Unchecked
            else:
                survey[0] = QtCore.Qt.Checked

        self.endResetModel()

        self._signal.filter.emit()


class SignalSurveys(QtCore.QObject):
    filter = QtCore.Signal()


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
