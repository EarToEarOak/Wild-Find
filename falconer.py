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

import os
import sys

from PySide import QtGui, QtCore

from falconer import ui
from falconer.database import Database
from falconer.heatmap import HeatMap
from falconer.log import DialogLog
from falconer.map import WidgetMap
from falconer.preferences import DialogPreferences
from falconer.printer import print_report
from falconer.scans import WidgetScans
from falconer.server import Server
from falconer.settings import Settings
from falconer.signals import WidgetSignals
from falconer.surveys import WidgetSurveys


class Falconer(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self._mapLoaded = False

        self.customWidgets = {'WidgetMap': WidgetMap,
                              'WidgetSurveys': WidgetSurveys,
                              'WidgetScans': WidgetScans,
                              'WidgetSignals': WidgetSignals}

        ui.loadUi(self, 'falconer.ui')

        self.splitter.setCollapsible(1, True)
        self.splitter.setCollapsible(2, True)

        self._settings = Settings(self,
                                  self._menuBar,
                                  self.__on_open_history)

        self._widgetSurveys.connect(self.__on_survey_filter)
        self._widgetScans.connect(self.__on_scan_filter)
        self._widgetSignals.connect(self.__on_signal_filter)
        self._widgetMap.connect(self.__on_signal_map_loaded,
                                self.__on_signal_map_colour)
        self._widgetMap.set_settings(self._settings)

        self._heatMap = HeatMap(self, self._settings,
                                self.__on_signal_map_plotted,
                                self.___on_signal_map_cleared)
        self._server = Server(self._heatMap.get_file())
        self._database = Database()

        self._printer = QtGui.QPrinter()
        self._printer.setCreator('Falconer')

        self.statusBar().showMessage('Ready')

    @QtCore.Slot()
    def on_actionNew_triggered(self):
        if not self.__file_warn():
            return

        dialog = QtGui.QFileDialog
        fileName, _ = dialog.getSaveFileName(self,
                                             'New file',
                                             filter='Database (*.db)')

        if fileName:
            if os.path.exists(fileName):
                os.remove(fileName)
            self.__open(fileName)

    @QtCore.Slot()
    def on_actionOpen_triggered(self):
        if not self.__file_warn():
            return

        dialog = QtGui.QFileDialog
        fileName, _ = dialog.getOpenFileName(self,
                                             filter='Database (*.db)')
        if fileName:
            self._settings.add_history(fileName)
            self.__open(fileName)

    @QtCore.Slot()
    def on_actionClose_triggered(self):
        self.__clear_scans()
        self._database.close()
        self.__set_controls()

    @QtCore.Slot()
    def on_actionExportPdf_triggered(self):
        printer = QtGui.QPrinter()
        self._printer.setDocName(self.windowTitle())
        printer.setOutputFormat(QtGui.QPrinter.PdfFormat)
        dialog = QtGui.QPrintPreviewDialog(printer, self)
        dialog.paintRequested.connect(self.__on__print)
        if dialog.exec_():
            self._printer = dialog.printer()

    @QtCore.Slot()
    def on_actionExportImage_triggered(self):
        dialog = QtGui.QFileDialog
        fileName, _ = dialog.getSaveFileName(self,
                                             'Export image',
                                             filter='PNG (*.png)')
        if fileName:
            mapImage = self._widgetMap.get_map()
            mapImage.save(fileName)

    @QtCore.Slot()
    def on_actionPrint_triggered(self):
        self._printer.setDocName(self.windowTitle())
        dialog = QtGui.QPrintPreviewDialog(self._printer, self)
        dialog.paintRequested.connect(self.__on__print)
        if dialog.exec_():
            self._printer = dialog.printer()

    @QtCore.Slot()
    def on_actionExit_triggered(self):
        self.close()

    @QtCore.Slot()
    def on_actionPreferences_triggered(self):
        dlg = DialogPreferences(self)
        dlg.show()

    @QtCore.Slot()
    def on_actionLog_triggered(self):
        dlg = DialogLog(self, self._database.get_logs())
        dlg.show()

    @QtCore.Slot(object)
    def __on_signal_map_plotted(self, bounds):
        self._widgetMap.update_heatmap(bounds)

    @QtCore.Slot()
    def ___on_signal_map_cleared(self):
        self._widgetMap.clear_heatmap()

    @QtCore.Slot()
    def __on_signal_map_loaded(self):
        self._mapLoaded = True
        self.__set_controls()

    @QtCore.Slot()
    def __on_signal_map_colour(self):
        self.__set_map()

    @QtCore.Slot(str)
    def __on_open_history(self, fileName):
        if not os.path.exists(fileName):
            message = 'File does not exist'
            QtGui.QMessageBox.question(self, 'Warning', message)
            return

        if not self.__file_warn():
            return

        self._settings.add_history(fileName)
        self.__open(fileName)

    @QtCore.Slot()
    def __on_survey_filter(self):
        self.__set_scans()
        self.__set_signals()
        self.__set_map()

    @QtCore.Slot()
    def __on_scan_filter(self):
        self.__set_signals()
        self.__set_map()

    @QtCore.Slot()
    def __on_signal_filter(self):
        self.__set_map()

    @QtCore.Slot(QtGui.QPrinter)
    def __on__print(self, printer):
        print_report(printer,
                     self._database.get_filename(),
                     self._widgetSurveys,
                     self._widgetScans,
                     self._widgetSignals,
                     self._widgetMap)

    def closeEvent(self, _event):
        self._settings.close()
        self._server.close()

    def __set_controls(self):
        if self._mapLoaded:
            self.actionOpen.setEnabled(True)
            self._menuRecent.setEnabled(True)

        enabled = False
        if self._database.isConnected():
            enabled = True

        self.actionExportPdf.setEnabled(enabled)
        self.actionExportImage.setEnabled(enabled)
        self.actionPrint.setEnabled(enabled)
        self.actionClose.setEnabled(enabled)

        self.actionLog.setEnabled(enabled)

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
        self.__clear_scans()

        error = self._database.open(fileName)
        if error is not None:
            QtGui.QMessageBox.critical(self,
                                       'Open failed',
                                       error)
            self.__clear_scans()
            return

        self.__set_surveys()
        self.__set_scans()
        self.__set_signals()
        self.__set_map()
        self.__set_controls()
        name = os.path.basename(fileName)
        self.setWindowTitle('Falconer - {}'.format(name))

    def __set_surveys(self):
        surveys = self._database.get_surveys()
        self._widgetSurveys.set(surveys)

    def __set_scans(self):
        filteredSurveys = self._widgetSurveys.get_filtered()
        scans = self._database.get_scans(filteredSurveys)
        self._widgetScans.set(scans)

    def __set_signals(self):
        filteredSurveys = self._widgetSurveys.get_filtered()
        filteredScans = self._widgetScans.get_filtered()
        signals = self._database.get_signals(filteredSurveys,
                                             filteredSurveys,
                                             filteredScans)
        self._widgetSignals.set(signals)

    def __set_map(self):
        self._widgetMap.show_busy(True)

        filteredSurveys = self._widgetSurveys.get_filtered()
        filteredScans = self._widgetScans.get_filtered()
        filteredSignals = self._widgetSignals.get_filtered()
        locations = self._database.get_locations(filteredSurveys,
                                                 filteredScans,
                                                 filteredSignals)
        self._widgetMap.set_locations(locations)

        telemetry = self._database.get_telemetry(filteredSurveys,
                                                 filteredScans,
                                                 filteredSignals)
        telemetry = self._widgetMap.transform_coords(telemetry)
        self._heatMap.set(telemetry)

    def __clear_scans(self):
        self._widgetSurveys.clear()
        self._widgetScans.clear()
        self._widgetSignals.clear()
        self._widgetMap.clear_locations()
        self._heatMap.set([])
        self.setWindowTitle('Falconer')


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
    mainWindow = Falconer()
    mainWindow.show()
    sys.exit(app.exec_())
