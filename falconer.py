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

import os
import sys

from PySide import QtGui, QtCore

from falconer import ui
from falconer.database import Database
from falconer.filters import WidgetFilters
from falconer.map import WidgetMap
from falconer.preferences import DialogPreferences
from falconer.server import Server
from falconer.signals import WidgetSignals
from falconer.settings import Settings


class Falconer(QtGui.QMainWindow):
    def __init__(self,):
        QtGui.QMainWindow.__init__(self)

        self.customWidgets = {'WidgetMap': WidgetMap,
                              'WidgetSignals': WidgetSignals,
                              'WidgetFilters': WidgetFilters}
        ui.loadUi(self, 'falconer.ui')
        self.splitter.setCollapsible(1, True)

        self._settings = Settings(self,
                                  self._menuBar,
                                  self.__on_actionHistory_triggered)
        self._server = Server()
        self._database = Database()

        self.statusBar().showMessage('Ready')

    @QtCore.Slot()
    def on_actionNew_triggered(self):
        dialog = QtGui.QFileDialog(self)
        dialog.setFileMode(QtGui.QFileDialog.AnyFile)
        dialog.setNameFilter('Database (*.db)')
        dialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
        dialog.setConfirmOverwrite(True)
        if dialog.exec_():
            fileName = dialog.selectedFiles()[0]
            if os.path.exists(fileName):
                os.remove(fileName)
            self._database.open(fileName)
            self.__set_signals()

    @QtCore.Slot()
    def on_actionOpen_triggered(self):
        dialog = QtGui.QFileDialog(self)
        dialog.setFileMode(QtGui.QFileDialog.AnyFile)
        dialog.setNameFilter('Database (*.db)')
        dialog.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
        if dialog.exec_():
            fileName = dialog.selectedFiles()[0]
            self._settings.add_history(fileName)
            self.__open(fileName)

    @QtCore.Slot(str)
    def __on_actionHistory_triggered(self, fileName):
        self.__open(fileName)

    @QtCore.Slot()
    def on_actionClose_triggered(self):
        self._database.close()
        self.__clear_signals()

    @QtCore.Slot()
    def on_actionExit_triggered(self):
        self.close()

    @QtCore.Slot()
    def on_actionPreferences_triggered(self):
        dlg = DialogPreferences(self)
        dlg.show()

    def closeEvent(self, _event):
        self._settings.close()
        self._server.close()

    def __open(self, fileName):
        self._database.open(fileName)
        self.__set_signals()

    def __set_signals(self):
        self._widgetSignals.set(self._database.get_frequencies())
        self._widgetFilters.set(self._database.get_scans())

    def __clear_signals(self):
        self._widgetSignals.clear()
        self._widgetFilters.clear()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
    mainWindow = Falconer()
    mainWindow.show()
    sys.exit(app.exec_())
