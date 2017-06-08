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

from PySide import QtCore

from wildfind.falconer.history import FileHistory

try:
    import mpl_toolkits.natgrid  # @UnusedImport
    NATGRID = True
except ImportError as error:
    NATGRID = False

MAX_REMOTE_HISTORY = 5


class Settings(object):
    def __init__(self, parent=None, menuBar=None, historyCallback=None):
        self._parent = parent

        if menuBar is None or historyCallback is None:
            self._history = None
        else:
            self._history = FileHistory(menuBar, historyCallback)

        self.style = 'Cleanlooks'

        self.dirFile = '.'
        self.dirExport = '.'

        self.remoteAddr = ''
        self.remoteHistory = []

        self.units = 'metric'

        self.fontList = None

        self.heatmapColour = 'jet'
        self.mapPos = [0, 0]
        self.mapZoom = 4

        self.interpolation = 'nn' if NATGRID else 'linear'

        self.__load()

    def __open(self):
        return QtCore.QSettings('Ear to Ear Oak', 'Falconer')

    def __load_array(self, arrayName):
        array = []
        settings = self.__open()
        size = settings.beginReadArray(arrayName)
        for i in range(size):
            settings.setArrayIndex(i)
            array.append(settings.value('{}'.format(i)))
        settings.endArray()

        return array

    def __save_array(self, arrayName, array):
        settings = self.__open()
        settings.beginWriteArray(arrayName)
        for i in range(len(array)):
            settings.setArrayIndex(i)
            settings.setValue('{}'.format(i), array[i])
        settings.endArray()

    def __load(self):
        settings = self.__open()

        self.style = settings.value('style', self.style)
        self.dirFile = settings.value('dirFile', self.dirFile)
        self.dirExport = settings.value('dirExport', self.dirExport)
        self.remoteAddr = settings.value('remoteAddr', self.remoteAddr)
        self.units = settings.value('units', self.units)
        self.fontList = settings.value('fontList', self.fontList)
        self.heatmapColour = settings.value('heatmapColour',
                                            self.heatmapColour)
        self.mapPos = settings.value('mapPos', self.mapPos)
        self.mapZoom = settings.value('mapZoom', self.mapZoom)

        if self._parent is not None:
            settings.beginGroup('MainWindow')
            size = settings.value('size')
            if size is not None:
                self._parent.resize(size)
            splitter = settings.value('splitter')
            if splitter is not None:
                self._parent.splitter.restoreState(splitter)
            settings.endGroup()

        if self._history is not None:
            history = self.__load_array('History')
            self._history.set(history)

        self.remoteHistory = self.__load_array('RemoteHistory')

        if NATGRID:
            self.interpolation = settings.value('interpolation',
                                                self.interpolation)

    def __save(self):
        settings = self.__open()

        settings.setValue('style', self.style)
        settings.setValue('dirFile', self.dirFile)
        settings.setValue('dirExport', self.dirExport)
        settings.setValue('remoteAddr', self.remoteAddr)
        settings.setValue('units', self.units)
        settings.setValue('fontList', self.fontList)
        settings.setValue('heatmapColour', self.heatmapColour)
        settings.setValue('mapPos', self.mapPos)
        settings.setValue('mapZoom', self.mapZoom)

        if self._parent is not None:
            settings.beginGroup('MainWindow')
            settings.setValue('size', self._parent.size())
            settings.setValue('splitter', self._parent.splitter.saveState())
            settings.endGroup()

        if self._history is not None:
            history = self._history.get()
            self.__save_array('History', history)

        self.__save_array('RemoteHistory', self.remoteHistory)

        settings.setValue('interpolation', self.interpolation)

    def add_history(self, fileName):
        self._history.add(fileName)

    def update_remote_history(self):
        while len(self.remoteHistory) > MAX_REMOTE_HISTORY:
            self.remoteHistory.pop()
        self.remoteHistory.append(self.remoteAddr)
        self.remoteHistory = list(set(self.remoteHistory))

    def close(self):
        self.__save()


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
