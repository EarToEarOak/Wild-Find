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

from PySide import QtCore, QtGui


class TableSelectionMenu(object):
    def __init__(self, table, model, addSelection=False):
        self._table = table
        self._model = model

        style = table.style()

        self._menu = QtGui.QMenu()

        actionAll = QtGui.QAction(table)
        actionAll.setText('Filter none')
        icon = style.standardIcon(QtGui.QStyle.SP_DialogYesButton)
        actionAll.setIcon(icon)
        actionAll.triggered.connect(self.on_all)
        self._menu.addAction(actionAll)

        actionNone = QtGui.QAction(table)
        actionNone.setText('Filter all')
        icon = style.standardIcon(QtGui.QStyle.SP_DialogNoButton)
        actionNone.setIcon(icon)
        actionNone.triggered.connect(self.on_none)
        self._menu.addAction(actionNone)

        actionInvert = QtGui.QAction(table)
        actionInvert.setText('Invert filters')
        actionInvert.triggered.connect(self.on_invert)
        self._menu.addAction(actionInvert)

        if addSelection:
            self._menu.addSeparator()
            actionSelClear = QtGui.QAction(table)
            actionSelClear.setText('Clear selection')
            icon = style.standardIcon(QtGui.QStyle.SP_DialogResetButton)
            actionSelClear.setIcon(icon)
            actionSelClear.triggered.connect(self.on_selection_clear)
            self._menu.addAction(actionSelClear)

        table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self.__contextMenu)

    @QtCore.Slot(QtCore.QPoint)
    def __contextMenu(self, pos):
        self._menu.exec_(self._table.mapToGlobal(pos))

    @QtCore.Slot()
    def on_all(self):
        self._model.set_filtered([])

    @QtCore.Slot()
    def on_none(self):
        self._model.set_filtered(self._model.get())

    @QtCore.Slot()
    def on_invert(self):
        filters = self._model.get()
        filtered = self._model.get_filtered()

        for value in filters:
            if value in filtered:
                filtered.remove(value)
            else:
                filtered.append(value)

        self._model.set_filtered(filtered)

    @QtCore.Slot()
    def on_selection_clear(self):
        self._table.clearSelection()


def remove_context_help(dialog):
    flags = dialog.windowFlags()
    dialog.setWindowFlags(flags & (~QtCore.Qt.WindowContextHelpButtonHint))


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
