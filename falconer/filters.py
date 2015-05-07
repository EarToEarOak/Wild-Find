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
        self._timeStamps = [0]

        ui.loadUi(self, 'filters.ui')

    @QtCore.Slot(QtCore.QDateTime)
    def on__timeFrom_dateTimeChanged(self, _dateTime):
        self.__set_range()

    @QtCore.Slot(QtCore.QDateTime)
    def on__timeTo_dateTimeChanged(self, _dateTime):
        pass

    def __set_range(self):
        timeMin = QtCore.QDateTime().fromTime_t(min(self._timeStamps))
        timeMax = QtCore.QDateTime().fromTime_t(max(self._timeStamps))

        self._timeFrom.setMinimumDateTime(timeMin)
        self._timeFrom.setMaximumDateTime(timeMax)

        timeMin = self._timeFrom.dateTime()
        self._timeTo.setMinimumDateTime(timeMin)
        self._timeTo.setMaximumDateTime(timeMax)

    def set(self, scans):
        self._timeStamps = [scan['TimeStamp'] for scan in scans]
        self.__set_range()

        self._from.setEnabled(True)
        self._to.setEnabled(True)

    def clear(self):
        self._from.setEnabled(False)
        self._to.setEnabled(False)


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
