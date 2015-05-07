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

        self._widgetFilters.set_callback_time(self.__on_signal_filter_time)

    @QtCore.Slot()
    def on_actionNew_triggered(self):
        if not self.__file_warn():
            return

        dialog = QtGui.QFileDialog(self)
        dialog.setFileMode(QtGui.QFileDialog.AnyFile)
        dialog.setNameFilter('Database (*.db)')
        dialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
        dialog.setConfirmOverwrite(True)
        if dialog.exec_():
            fileName = dialog.selectedFiles()[0]
            if os.path.exists(fileName):
                os.remove(fileName)
            self.__open(fileName)

    @QtCore.Slot()
    def on_actionOpen_triggered(self):
        if not self.__file_warn():
            return

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
        if not self.__file_warn():
            return

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

    @QtCore.Slot(bool, bool, float, float)
    def __on_signal_filter_time(self, fromEnabled, toEnabled, fromTime, toTime):
        timeRange = (fromEnabled, toEnabled, fromTime, toTime)
        self.__set_signals(timeRange)

    def closeEvent(self, _event):
        self._settings.close()
        self._server.close()

    def __file_warn(self):
        if self._database.isConnected():
            flags = (QtGui.QMessageBox.StandardButton.Yes |
                     QtGui.QMessageBox.StandardButton.No)
            message = 'Close existing file?'
            response = QtGui.QMessageBox.question(self, 'Warning',
                                                  message,
                                                  flags)
            if response == QtGui.QMessageBox.No:
                return False

        return True

    def __open(self, fileName):
        self._database.open(fileName)
        self.__set_signals()

    def __set_signals(self, timeRange=None):
        frequencies = self._database.get_frequencies(timeRange)
        scans = self._database.get_scans()
        self._widgetSignals.set(frequencies)
        self._widgetFilters.set(scans)

    def __clear_signals(self):
        self._widgetSignals.clear()
        self._widgetFilters.clear()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
    mainWindow = Falconer()
    mainWindow.show()
    sys.exit(app.exec_())
