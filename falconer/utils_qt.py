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

from PySide import QtCore, QtGui


class TableSelectionMenu(object):
    def __init__(self, table, model):
        self._table = table
        self._model = model

        table.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        actionAll = QtGui.QAction(table)
        actionAll.setText('Select all')
        actionAll.triggered.connect(self.on_all)
        table.addAction(actionAll)

        actionNone = QtGui.QAction(table)
        actionNone.setText('Select none')
        actionNone.triggered.connect(self.on_none)
        table.addAction(actionNone)

        actionInvert = QtGui.QAction(table)
        actionInvert.setText('Invert selection')
        actionInvert.triggered.connect(self.on_invert)
        table.addAction(actionInvert)

    @QtCore.Slot()
    def on_all(self):
        self._model.set_filtered([])

    @QtCore.Slot()
    def on_none(self):
        self._model.set_filtered(self._model.get_filters())

    @QtCore.Slot()
    def on_invert(self):
        filters = self._model.get_filters()
        filtered = self._model.get_filtered()

        for value in filters:
            if value in filtered:
                filtered.remove(value)
            else:
                filtered.append(value)

        self._model.set_filtered(filtered)


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
