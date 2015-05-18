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
from falconer.utils_qt import remove_context_help


class DialogPreferences(QtGui.QDialog):
    def __init__(self, parent, settings):
        QtGui.QDialog.__init__(self, parent)

        remove_context_help(self)

        self._settings = settings

        ui.loadUi(self, 'preferences.ui')

        styles = QtGui.QStyleFactory.keys()
        style = QtGui.QApplication.style().objectName()
        self._comboStyles.addItems(styles)
        index = ([name.lower() for name in styles]).index(style)
        self._comboStyles.setCurrentIndex(index)

        units = ['Metric', 'Imperial', 'Nautical']
        self._comboUnits.addItems(units)
        index = ([unit.lower() for unit in units]).index(self._settings.units.lower())
        self._comboUnits.setCurrentIndex(index)

    @QtCore.Slot(str)
    def on__comboStyles_activated(self, styleName):
        style = QtGui.QStyleFactory.create(styleName)
        QtGui.QApplication.setStyle(style)

    @QtCore.Slot()
    def on__buttonBox_accepted(self):
        self._settings.style = self._comboStyles.currentText()
        self._settings.units = self._comboUnits.currentText()
        self.accept()


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
