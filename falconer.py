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
from falconer.heatmap import HeatMap
from falconer.map import WidgetMap
from falconer.preferences import DialogPreferences
from falconer.scans import WidgetScans
from falconer.server import Server
from falconer.settings import Settings
from falconer.signals import WidgetSignals


class Falconer(QtGui.QMainWindow):
    def __init__(self,):
        QtGui.QMainWindow.__init__(self)

        self.customWidgets = {'WidgetMap': WidgetMap,
                              'WidgetScans': WidgetScans,
                              'WidgetSignals': WidgetSignals}

        ui.loadUi(self, 'falconer.ui')

        self.splitter.setCollapsible(1, True)
        self.splitter.setCollapsible(2, True)

        self._widgetScans.connect(self.__on_scan_filter)
        self._widgetSignals.connect(self.__on_signal_filter)

        self._settings = Settings(self,
                                  self._menuBar,
                                  self.__on_open_history)

        self._heatMap = HeatMap(self, self.__on_heatmap)
        self._server = Server(self._heatMap.get_file())
        self._database = Database()

        self.statusBar().showMessage('Ready')

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

    @QtCore.Slot()
    def on_actionClose_triggered(self):
        self._database.close()
        self.__clear_scans()

    @QtCore.Slot()
    def on_actionExit_triggered(self):
        self.close()

    @QtCore.Slot()
    def on_actionPreferences_triggered(self):
        dlg = DialogPreferences(self)
        dlg.show()

    @QtCore.Slot(str)
    def __on_open_history(self, fileName):
        if not self.__file_warn():
            return

        self.__open(fileName)

    @QtCore.Slot()
    def __on_scan_filter(self):
        self.__set_signals()
        self.__set_map()

    @QtCore.Slot()
    def __on_signal_filter(self):
        self.__set_map()

    @QtCore.Slot(object)
    def __on_heatmap(self, bounds):
        self._widgetMap.update_heatmap(bounds)

    @QtCore.Slot(QtGui.QCloseEvent)
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
        self.__clear_scans()
        self.__set_scans()
        self.__set_signals()
        self.__set_map()

    def __set_scans(self):
        scans = self._database.get_scans()
        self._widgetScans.set(scans)

    def __set_signals(self):
        filtered = self._widgetScans.get_filtered()
        signals = self._database.get_signals(filtered)
        self._widgetSignals.set(signals)

    def __set_map(self):
        filteredScans = self._widgetScans.get_filtered()
        filteredSignals = self._widgetSignals.get_filtered()
        locations = self._database.get_locations(filteredScans,
                                                 filteredSignals)
        self._widgetMap.set_locations(locations)

        telemetry = self._database.get_telemetry(filteredScans,
                                                 filteredSignals)
        self._heatMap.set(telemetry)

    def __clear_scans(self):
        self._widgetScans.clear()
        self._widgetSignals.clear()
        self._widgetMap.clear()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
    mainWindow = Falconer()
    mainWindow.show()
    sys.exit(app.exec_())
