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

import argparse
import os
import socket
import sys

from PySide import QtGui, QtCore

from falconer import ui
from falconer.about import DialogAbout
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
from falconer.utils import export_kml
from falconer.utils_qt import remove_context_help


class Falconer(QtGui.QMainWindow):
    def __init__(self, args):
        QtGui.QMainWindow.__init__(self)
        self._args = args

        self._mapLoaded = False
        self._fullScreen = False

        self.customWidgets = {'WidgetMap': WidgetMap,
                              'WidgetSurveys': WidgetSurveys,
                              'WidgetScans': WidgetScans,
                              'WidgetSignals': WidgetSignals}

        ui.loadUi(self, 'falconer.ui')

        self.splitter.splitterMoved.connect(self.__on_splitter_moved)
        self.splitter.setCollapsible(1, True)
        self.splitter.setCollapsible(2, True)
        self.splitter.setCollapsible(3, True)

        self._settings = Settings(self,
                                  self._menubar,
                                  self.__on_open_history)

        self._widgetSurveys.connect(self.__on_survey_filter)
        self._widgetScans.connect(self.__on_scan_filter)
        self._widgetSignals.connect(self.__on_signal_filter,
                                    self.__on_signal_select)
        self._widgetMap.connect(self.__on_signal_map_loaded,
                                self.__on_signal_map_colour,
                                self.__on_signal_map_selected)
        self._widgetMap.set_settings(self._settings)

        self._heatMap = HeatMap(self, self._settings,
                                self.__on_signal_map_plotted,
                                self.__on_signal_map_cleared)

        self._server = None
        self.__start_server()
        self._database = Database()

        self._printer = QtGui.QPrinter()
        self._printer.setCreator('Falconer')

        self.__set_icons()
        self.__set_fonts()
        self.__set_table_view()

        self.setAcceptDrops(True)

        self._statusbar.showMessage('Ready')

        self.show()

    def __set_icons(self):
        style = self.style()

        icon = style.standardIcon(QtGui.QStyle.SP_DialogSaveButton)
        self.actionNew.setIcon(icon)

        icon = style.standardIcon(QtGui.QStyle.SP_DialogOpenButton)
        self.actionOpen.setIcon(icon)

        icon = style.standardIcon(QtGui.QStyle.SP_DialogCloseButton)
        self.actionClose.setIcon(icon)

        icon = style.standardIcon(QtGui.QStyle.SP_MessageBoxQuestion)
        self.actionHelp.setIcon(icon)

        icon = style.standardIcon(QtGui.QStyle.SP_MessageBoxInformation)
        self.actionAbout.setIcon(icon)

    def __set_fonts(self):
        if self._settings.fontList is None:
            self._settings.fontList = self._widgetSurveys.get_font()

        self._widgetSurveys.set_font(self._settings.fontList)
        self._widgetScans.set_font(self._settings.fontList)
        self._widgetSignals.set_font(self._settings.fontList)

    def __start_server(self):
        try:
            self._server = Server(self._heatMap.get_file())
        except socket.error:
            QtGui.QMessageBox.warning(self, 'Warning',
                                      'Falconer is already running',
                                      QtGui.QMessageBox.Ok)

            self.close()
            exit(1)

    @QtCore.Slot()
    def on_actionNew_triggered(self):
        dialog = QtGui.QFileDialog
        fileName, _ = dialog.getSaveFileName(self,
                                             'New file',
                                             dir=self._settings.dirFile,
                                             filter='Wild Find file (*.wfh)')

        if fileName:
            self._settings.dirFile, _ = os.path.split(fileName)
            if os.path.exists(fileName):
                os.remove(fileName)
            self.__open(fileName)

    @QtCore.Slot()
    def on_actionOpen_triggered(self):
        dialog = QtGui.QFileDialog
        fileName, _ = dialog.getOpenFileName(self,
                                             dir=self._settings.dirFile,
                                             filter='Wild Find file (*.wfh)')
        if fileName:
            self._settings.dirFile, _ = os.path.split(fileName)
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
        remove_context_help(dialog)
        dialog.paintRequested.connect(self.__on__print)
        if dialog.exec_():
            self._printer = dialog.printer()

    @QtCore.Slot()
    def on_actionExportImage_triggered(self):
        filters = ('Windows Bitmap (*.bmp);;'
                   'JPEG (*.jpg);;'
                   'Portable Network Graphics (*.png);;'
                   'Portable Pixmap (.ppm);;'
                   'Tagged Image File Format (*.tiff);;'
                   'X11 Bitmap (*.xbm);;'
                   'X11 Pixmap (.xpm)')
        dialog = QtGui.QFileDialog
        fileName, _ = dialog.getSaveFileName(self,
                                             'Export image',
                                             dir=self._settings.dirExport,
                                             filter=filters,
                                             selectedFilter='Portable Network Graphics (*.png)')
        if fileName:
            self._settings.dirExport, _ = os.path.split(fileName)
            mapImage = self._widgetMap.get_map()
            mapImage.save(fileName)

    @QtCore.Slot()
    def on_actionExportKml_triggered(self):
        filter = 'Keyhole Markup Language (*.kmz)'
        dialog = QtGui.QFileDialog
        fileName, _ = dialog.getSaveFileName(self,
                                             'Export KML',
                                             dir=self._settings.dirExport,
                                             filter=filter)
        if fileName:
            self._settings.dirExport, _ = os.path.split(fileName)
            filteredSurveys = self._widgetSurveys.get_filtered()
            filteredScans = self._widgetScans.get_filtered()
            filteredSignals = self._widgetSignals.get_filtered()
            telemetry = self._database.get_telemetry(filteredSurveys,
                                                     filteredScans,
                                                     filteredSignals)

            export_kml(fileName, self._heatMap.get_file(), telemetry)

    @QtCore.Slot()
    def on_actionPrint_triggered(self):
        self._printer.setDocName(self.windowTitle())
        dialog = QtGui.QPrintPreviewDialog(self._printer, self)
        remove_context_help(dialog)
        dialog.paintRequested.connect(self.__on__print)
        if dialog.exec_():
            self._printer = dialog.printer()

    @QtCore.Slot()
    def on_actionExit_triggered(self):
        self.close()

    @QtCore.Slot()
    def on_actionPreferences_triggered(self):
        dlg = DialogPreferences(self, self._settings)
        if dlg.exec_():
            self._widgetMap.set_units(self._settings.units)
            self.__set_fonts()

    @QtCore.Slot(bool)
    def on_actionViewSurveys_triggered(self, checked):
        sizes = self.splitter.sizes()
        sizes[1] = 9999 * checked
        self.splitter.setSizes(sizes)

    @QtCore.Slot(bool)
    def on_actionViewScans_triggered(self, checked):
        sizes = self.splitter.sizes()
        sizes[2] = 9999 * checked
        self.splitter.setSizes(sizes)

    @QtCore.Slot(bool)
    def on_actionViewSignals_triggered(self, checked):
        sizes = self.splitter.sizes()
        sizes[3] = 9999 * checked
        self.splitter.setSizes(sizes)

    @QtCore.Slot()
    def on_actionLog_triggered(self):
        dlg = DialogLog(self, self._database.get_logs())
        dlg.exec_()

    @QtCore.Slot()
    def on_actionFullscreen_triggered(self):
        self.__fullscreen()

    @QtCore.Slot()
    def on_actionAbout_triggered(self):
        dlg = DialogAbout(self)
        dlg.exec_()

    @QtCore.Slot()
    def __on_splitter_moved(self, _pos, _index):
        self.__set_table_view()

    @QtCore.Slot()
    def __on_signal_map_loaded(self):
        self._mapLoaded = True
        self._widgetMap.set_pos(self._settings.mapPos, self._settings.mapZoom)
        self._widgetMap.set_units(self._settings.units)
        self._widgetMap.show_busy(False)
        self.__set_controls()

        fileName = self._args.file
        if fileName is not None:
            self._args.file = None
            self.__open(fileName)

    @QtCore.Slot(object)
    def __on_signal_map_plotted(self, bounds):
        if self._database.isConnected():
            self._widgetMap.set_heatmap(bounds)

    @QtCore.Slot()
    def __on_signal_map_cleared(self):
        self._widgetMap.clear_heatmap()

    @QtCore.Slot()
    def __on_signal_map_colour(self):
        self.__set_map()

    @QtCore.Slot(list)
    def __on_signal_map_selected(self, frequencies):
        freqs = set(frequencies)
        self._widgetSignals.select(list(freqs))

    @QtCore.Slot(str)
    def __on_open_history(self, fileName):
        if self.__open(fileName):
            self._settings.add_history(fileName)

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

    @QtCore.Slot(list)
    def __on_signal_select(self, frequencies):
        self._widgetMap.select_locations(frequencies)

    @QtCore.Slot(QtGui.QPrinter)
    def __on__print(self, printer):
        print_report(printer,
                     self._database.get_filename(),
                     self._widgetSurveys,
                     self._widgetScans,
                     self._widgetSignals,
                     self._widgetMap)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls):
                fileName = urls[0].path()
                _, ext = os.path.splitext(fileName)
                if ext == '.wfh':
                    event.accept()
                    return

        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if len(urls):
            filename = urls[0].path().lstrip('/')
            self.__open(filename)

    def closeEvent(self, _event):
        self._fullScreen = True
        self.__fullscreen()
        pos = self._widgetMap.get_pos()
        if pos is not None:
            self._settings.mapPos = pos[0]
            self._settings.mapZoom = pos[1]
        self._settings.close()
        if self._server is not None:
            self._server.close()

    def __fullscreen(self):
        self._statusbar.setVisible(self._fullScreen)
        self._toolbarControls.setVisible(self._fullScreen)

        self._widgetSurveys.setVisible(self._fullScreen)
        self._widgetScans.setVisible(self._fullScreen)
        self._widgetSignals.setVisible(self._fullScreen)

        self._fullScreen = not self._fullScreen
        if self._fullScreen:
            self.showFullScreen()
        else:
            self.showNormal()

    def __set_controls(self):
        if self._mapLoaded:
            self.actionOpen.setEnabled(True)
            self._menuRecent.setEnabled(True)
            self.actionPreferences.setEnabled(True)

        enabled = False
        if self._database is not None and self._database.isConnected():
            enabled = True

        self.actionExportPdf.setEnabled(enabled)
        self.actionExportImage.setEnabled(enabled)
        self.actionExportKml.setEnabled(enabled)
        self.actionPrint.setEnabled(enabled)
        self.actionClose.setEnabled(enabled)

        self.actionLog.setEnabled(enabled)

    def __set_table_view(self):
        sizes = self.splitter.sizes()
        self.actionViewSurveys.setChecked(sizes[1] != 0)
        self.actionViewScans.setChecked(sizes[2] != 0)
        self.actionViewSignals.setChecked(sizes[3] != 0)

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
        if not os.path.exists(fileName):
            message = 'File not found'
            QtGui.QMessageBox.warning(self, 'Warning', message)
            return

        if not self.__file_warn():
            return False

        self.__clear_scans()

        error = self._database.open(fileName)
        if error is not None:
            QtGui.QMessageBox.critical(self,
                                       'Open failed',
                                       error)
            self.__clear_scans()
            return False

        self.__set_surveys()
        self.__set_scans()
        self.__set_signals()
        self.__set_map()
        self.__set_controls()
        name = os.path.basename(fileName)
        self.setWindowTitle('Falconer - {}'.format(name))

        return True

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


def __arguments():
    parser = argparse.ArgumentParser(description='Falconer')
    parser.add_argument("file", help='Database path', nargs='?', default=None)

    args, unknown = parser.parse_known_args()

    return args, unknown


if __name__ == '__main__':
    args, argsApp = __arguments()

    app = QtGui.QApplication(argsApp)
    settings = Settings()
    QtGui.QApplication.setStyle(settings.style)
    mainWindow = Falconer(args)
    sys.exit(app.exec_())
