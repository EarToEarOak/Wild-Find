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
from falconer.table import Model
from falconer.utils_qt import TableSelectionMenu


class WidgetSurveys(QtGui.QWidget):
    HEADER = [None, 'Name']
    HEADER_TIPS = ['Included', 'Survey name']

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self._signal = SignalSurveys()

        ui.loadUi(self, 'surveys.ui')

        self._model = Model(self._signal, self.HEADER, self.HEADER_TIPS)
        proxyModel = QtGui.QSortFilterProxyModel(self)
        proxyModel.setDynamicSortFilter(True)
        proxyModel.setSourceModel(self._model)

        self._tableSurveys.setModel(proxyModel)
        self._contextMenu = TableSelectionMenu(self._tableSurveys,
                                               self._model)

        self.__set_width()

    def __set_width(self):
        self._tableSurveys.resizeColumnsToContents()

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

    def __on_filter(self):
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

    def connect(self, slot):
        self._signal.filter.connect(slot)

    def set(self, surveys):
        self._model.set(surveys)
        self.__set_width()

        self._comboSurveys.clear()
        self._comboSurveys.addItem('All')
        self._comboSurveys.addItems(surveys)

        self._tableSurveys.setEnabled(True)
        self._comboSurveys.setEnabled(True)

    def set_font(self, font):
        newFont = QtGui.QFont()
        newFont.fromString(font)
        self._tableSurveys.setFont(newFont)
        self.__set_width()

    def get(self):
        return self._model.get()

    def get_filtered(self):
        return self._model.get_filtered()

    def get_font(self):
        return self._tableSurveys.font().toString()

    def clear(self):
        self._model.set([])
        self._model.set_filtered([])
        self._tableSurveys.setEnabled(False)
        self._comboSurveys.setEnabled(False)


class SignalSurveys(QtCore.QObject):
    filter = QtCore.Signal()


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
