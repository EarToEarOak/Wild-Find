#!/usr/bin/env python
#
#
# Wild Find
#
#
# Copyright 2014 - 2017 Al Brown
#
# Wildlife tracking and mapping
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation
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

from wildfind.falconer import ui
from wildfind.falconer.utils_qt import win_remove_context_help

try:
    import mpl_toolkits.natgrid  # @UnusedImport
    NATGRID = True
except ImportError as error:
    NATGRID = False


class DialogPreferences(QtGui.QDialog):
    def __init__(self, parent, settings):
        QtGui.QDialog.__init__(self, parent)

        self._settings = settings

        ui.loadUi(self, 'preferences.ui')
        win_remove_context_help(self)

        styles = QtGui.QStyleFactory.keys()
        style = QtGui.QApplication.style().objectName()
        self._comboStyles.addItems(styles)
        index = ([name.lower() for name in styles]).index(style)
        self._comboStyles.setCurrentIndex(index)

        units = ['Metric', 'Imperial', 'Nautical']
        self._comboUnits.addItems(units)
        index = ([unit.lower()
                  for unit in units]).index(self._settings.units.lower())
        self._comboUnits.setCurrentIndex(index)

        self._font = QtGui.QFont()
        self._font.fromString(settings.fontList)
        self._buttonFont.setText(self.__font_name())

        if NATGRID:
            interp = ['Linear', 'Nearest neighbour']
            self._comboInterp.addItems(interp)
            self._comboInterp.setCurrentIndex(1 if self._settings.interpolation == 'nn' else 0)
        else:
            self._labelInterp.hide()
            self._comboInterp.hide()

    @QtCore.Slot(str)
    def on__comboStyles_activated(self, styleName):
        style = QtGui.QStyleFactory.create(styleName)
        QtGui.QApplication.setStyle(style)

    @QtCore.Slot(bool)
    def on__buttonFont_clicked(self, _clicked):
        font, ok = QtGui.QFontDialog.getFont(self._font, self)
        if ok:
            self._font = font
            self._buttonFont.setText(self.__font_name())

    @QtCore.Slot()
    def on__buttonBox_accepted(self):
        self._settings.style = self._comboStyles.currentText()
        self._settings.units = self._comboUnits.currentText()
        self._settings.fontList = self._font.toString()
        if NATGRID:
            self._settings.interpolation = 'linear' if self._comboInterp.currentIndex() == 0 else 'nn'
        else:
            self._settings.interpolation = 'linear'

        self.accept()

    def __font_name(self):
        desc = self._font.toString().split(',')[0:2]
        return '{} {}pt'.format(*desc)


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
