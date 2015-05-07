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


class DialogPreferences(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)

        ui.loadUi(self, 'preferences.ui')

        self._comboStyles.addItems(QtGui.QStyleFactory.keys())

    @QtCore.Slot(str)
    def on__comboStyles_activated(self, styleName):
        style = QtGui.QStyleFactory.create(styleName)
        QtGui.QApplication.setStyle(style)


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
