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

from PySide import QtCore, QtGui, QtWebKit

from falconer import ui


class TableSelectionMenu(object):
    def __init__(self, table, model, hasSelection=None):
        self._table = table
        self._model = model
        self._hasSelection = hasSelection
        self._menu = None

        table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self.__context_menu)

    def __context_menu(self, pos):
        style = self._table.style()
        filters = len(self._model.get())
        filtered = len(self._model.get_filtered())

        self._menu = QtGui.QMenu()

        actionNone = QtGui.QAction(self._table)
        actionNone.setText('Filter none')
        icon = style.standardIcon(QtGui.QStyle.SP_DialogYesButton)
        actionNone.setIcon(icon)
        actionNone.triggered.connect(self.on_all)
        self._menu.addAction(actionNone)
        if not filtered:
            actionNone.setEnabled(False)

        actionAll = QtGui.QAction(self._table)
        actionAll.setText('Filter all')
        icon = style.standardIcon(QtGui.QStyle.SP_DialogNoButton)
        actionAll.setIcon(icon)
        actionAll.triggered.connect(self.on_none)
        self._menu.addAction(actionAll)
        if filters == filtered:
            actionAll.setEnabled(False)

        actionInvert = QtGui.QAction(self._table)
        actionInvert.setText('Invert filters')
        actionInvert.triggered.connect(self.on_invert)
        self._menu.addAction(actionInvert)

        if self._hasSelection is not None:
            self._menu.addSeparator()
            actionSelClear = QtGui.QAction(self._table)
            actionSelClear.setText('Clear selection')
            icon = style.standardIcon(QtGui.QStyle.SP_DialogResetButton)
            actionSelClear.setIcon(icon)
            actionSelClear.triggered.connect(self.on_selection_clear)
            self._menu.addAction(actionSelClear)
            actionSelClear.setEnabled(self._hasSelection())

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


class DialogPopup(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)

        ui.loadUi(self, 'popup.ui')

        self.setWindowFlags(QtCore.Qt.Tool)

        self._web.titleChanged.connect(self.__on_title)

    def __on_title(self, title):
        self.setWindowTitle(title)

    def load(self, url):
        self._web.load(url)


def win_remove_context_help(window):
    flags = window.windowFlags()
    window.setWindowFlags(flags & (~QtCore.Qt.WindowContextHelpButtonHint))


def win_set_maximise(window):
    window.setWindowFlags(QtCore.Qt.WindowMaximizeButtonHint)


def win_set_icon(window):
    top = QtGui.QApplication.topLevelWidgets()[0]
    window.setWindowIcon(top.windowIcon())


def cal_set_colours(calendar):
    palette = calendar.palette()
    palette.setColor(QtGui.QPalette.Window, QtCore.Qt.lightGray)
    palette.setColor(QtGui.QPalette.Base, QtCore.Qt.white)
    colour = QtGui.QColor(240, 240, 240)
    palette.setColor(QtGui.QPalette.AlternateBase, colour)
    calendar.setPalette(palette)


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
