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

from PySide import QtCore

from falconer.history import FileHistory


class Settings(object):
    def __init__(self, parent, menuBar, historyCallback):
        self._parent = parent
        self._history = FileHistory(menuBar, historyCallback)

        self.heatmapColour = 'jet'

        self.__load()

    def __open(self):
        return QtCore.QSettings('Ear to Ear Oak', 'Falconer')

    def __load_history(self):
        history = []

        settings = self.__open()
        settings.beginGroup('History')
        files = settings.value('files', 0)
        for i in range(int(files)):
            history.append(settings.value('{}'.format(i)))
        settings.endGroup()
        self._history.set(history)

    def __save_history(self):
        settings = self.__open()
        settings.beginGroup('History')
        history = self._history.get()
        settings.setValue('files', len(history))
        for i in range(len(history)):
            settings.setValue('{}'.format(i), history[i])
        settings.endGroup()

    def __load(self):
        settings = self.__open()
        self.heatmapColour = settings.value('heatmapColour', 'jet')
        settings.beginGroup('MainWindow')
        size = settings.value('size')
        if size is not None:
            self._parent.resize(size)
        splitter = settings.value('splitter')
        if splitter is not None:
            self._parent.splitter.restoreState(splitter)
        settings.endGroup()

        self.__load_history()

    def __save(self):
        settings = self.__open()

        settings.setValue('heatmapColour', self.heatmapColour)

        settings.beginGroup('MainWindow')
        settings.setValue('size', self._parent.size())
        settings.setValue('splitter', self._parent.splitter.saveState())
        settings.endGroup()

        self.__save_history()

    def add_history(self, fileName):
        self._history.add(fileName)

    def close(self):
        self.__save()


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
