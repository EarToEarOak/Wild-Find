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


class WidgetFilters(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self._callback = None
        self._timeMin = None
        self._timeMax = None

        self._signal = FilterSignal()

        ui.loadUi(self, 'filters.ui')

    @QtCore.Slot(int)
    def on__checkFrom_stateChanged(self, _state):
        checked = self._checkFrom.isChecked()
        self._timeFrom.setEnabled(checked)
        self.__fire_time()

    @QtCore.Slot(int)
    def on__checkTo_stateChanged(self, _state):
        checked = self._checkTo.isChecked()
        self._timeTo.setEnabled(checked)
        self.__fire_time()

    @QtCore.Slot(QtCore.QDateTime)
    def on__timeFrom_dateTimeChanged(self, _dateTime):
        self.__set_time_limits()
        self.__fire_time()

    @QtCore.Slot(QtCore.QDateTime)
    def on__timeTo_dateTimeChanged(self, _dateTime):
        self.__set_time_limits()
        self.__fire_time()

    def __block_time_signals(self, block):
        self._timeFrom.blockSignals(block)
        self._timeTo.blockSignals(block)

    def __set_time_limits(self):
        self.__block_time_signals(True)

        self._timeFrom.setMinimumDateTime(self._timeMin)
        timeMin = self._timeFrom.dateTime()
        self._timeTo.setMinimumDateTime(timeMin)

        self._timeTo.setMaximumDateTime(self._timeMax)
        timeMax = self._timeTo.dateTime()
        self._timeFrom.setMaximumDateTime(timeMax)

        self.__block_time_signals(False)

    def __set_time_full(self):
        self.__block_time_signals(True)
        self._timeFrom.setDateTime(self._timeMin)
        self._timeTo.setDateTime(self._timeMax)
        self.__block_time_signals(False)

    def __fire_time(self):
        fromChecked = self._checkFrom.isChecked()
        toChecked = self._checkTo.isChecked()
        fromTime = self._timeFrom.dateTime().toTime_t()
        toTime = self._timeTo.dateTime().toTime_t()
        self._signal.time[bool, bool, float, float].emit(fromChecked,
                                                         toChecked,
                                                         fromTime,
                                                         toTime)

    def set_callback_time(self, callback):
        self._signal.time[bool, bool, float, float].connect(callback)

    def set(self, scans):
        timeStamps = [scan['TimeStamp'] for scan in scans]
        self._timeMin = QtCore.QDateTime().fromTime_t(min(timeStamps))
        self._timeMax = QtCore.QDateTime().fromTime_t(max(timeStamps))

        self.__set_time_limits()
        self.__set_time_full()

        self.setEnabled(True)

    def clear(self):
        self.setEnabled(False)


class FilterSignal(QtCore.QObject):
    time = QtCore.Signal(bool, bool, float, float)



if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
