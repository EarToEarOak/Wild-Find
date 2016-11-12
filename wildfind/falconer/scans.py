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
from falconer.table import Model, format_qtime
from falconer.utils_qt import TableSelectionMenu, win_remove_context_help,\
    cal_set_colours


class WidgetScans(QtGui.QWidget):
    HEADER = [None, 'Time', 'Freq']
    HEADER_TIPS = ['Included', 'Scan time', 'Scan frequency (MHz)']

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self._signal = SignalScans()

        ui.loadUi(self, 'scans.ui')

        formatters = [None, format_qtime, None]
        self._model = Model(self._signal, self.HEADER, self.HEADER_TIPS,
                            formatters)
        proxyModel = QtGui.QSortFilterProxyModel(self)
        proxyModel.setDynamicSortFilter(True)
        proxyModel.setSourceModel(self._model)

        self._tableScans.setModel(proxyModel)
        self._contextMenu = TableSelectionMenu(self._tableScans,
                                               self._model)

        self.__set_width()

    def __set_width(self):
        self._tableScans.resizeColumnsToContents()

        margins = self.layout().contentsMargins()
        width = self._tableScans.verticalHeader().width()
        width += self._tableScans.horizontalHeader().length()
        width += self._tableScans.style().pixelMetric(QtGui.QStyle.PM_ScrollBarExtent)
        width += self._tableScans.frameWidth() * 2
        width += margins.left() + margins.right()
        width += self.layout().spacing()
        self.setMaximumWidth(width)

    @QtCore.Slot(bool)
    def on__buttonRange_clicked(self, _clicked):
        timeStamps = self._model.get()
        dialog = DialogScansRange(self, timeStamps)
        if dialog.exec_():
            filtered = dialog.get_filtered()
            self._model.set_filtered(filtered)

    def connect(self, slot):
        self._model.connect(slot)

    def set(self, scans):
        self._model.set(scans)
        self.__set_width()

        self._tableScans.setEnabled(True)
        self._buttonRange.setEnabled(True)

    def set_font(self, font):
        newFont = QtGui.QFont()
        newFont.fromString(font)
        self._tableScans.setFont(newFont)
        self.__set_width()

    def get(self):
        return self._model.get()

    def get_filtered(self):
        return self._model.get_filtered()

    def clear(self):
        self._model.set([])
        self._model.set_filtered([], False)
        self._tableScans.setEnabled(False)
        self._buttonRange.setEnabled(False)


class DialogScansRange(QtGui.QDialog):
    def __init__(self, parent, timeStamps):
        QtGui.QDialog.__init__(self, parent)
        self._timeStamps = timeStamps

        ui.loadUi(self, 'scans_range.ui')
        win_remove_context_help(self)

        timeMin, timeMax = self.__get_range()
        self._timeFrom = timeMin.toTime_t()
        self._timeTo = timeMax.toTime_t()

        self._dateFrom.setDateTimeRange(timeMin, timeMax)
        self._dateFrom.setDateTime(timeMin)
        self._dateTo.setDateTimeRange(timeMin, timeMax)
        self._dateTo.setDateTime(timeMax)

        cal_set_colours(self._dateFrom)
        cal_set_colours(self._dateTo)

    @QtCore.Slot(QtCore.QDateTime)
    def on__dateFrom_dateTimeChanged(self, dateTime):
        _timeMin, timeMax = self.__get_range()
        self._timeFrom = dateTime.toTime_t()
        self._dateTo.setDateTimeRange(dateTime, timeMax)

    @QtCore.Slot(QtCore.QDateTime)
    def on__dateTo_dateTimeChanged(self, dateTime):
        self._timeTo = dateTime.toTime_t()

    @QtCore.Slot()
    def on__buttonBox_accepted(self):
        self.accept()

    @QtCore.Slot()
    def on__buttonBox_rejected(self):
        self.reject()

    def __get_range(self):
        timeMin = QtCore.QDateTime.fromTime_t(min(self._timeStamps))
        timeMax = QtCore.QDateTime.fromTime_t(max(self._timeStamps))

        return timeMin, timeMax

    def get_filtered(self):
        filtered = []
        for timeStamp in self._timeStamps:
            if timeStamp < self._timeFrom or timeStamp > self._timeTo:
                filtered.append(timeStamp)

        return filtered


class SignalScans(QtCore.QObject):
    filter = QtCore.Signal()


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
