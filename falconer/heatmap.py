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

import copy
import tempfile
import warnings

from PySide import QtCore
import matplotlib
import numpy

matplotlib.use("Agg")
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt


IMAGE_SIZE = 300


class HeatMap(QtCore.QObject):
    def __init__(self, parent, settings, on_plotted, on_cleared):
        QtCore.QObject.__init__(self, parent)
        self._settings = settings

        self._telemetry = None

        self._thread = None
        self._tempFile = tempfile.TemporaryFile(suffix='.png')

        self._signal = SignalPlot()
        self._signal.plotted.connect(on_plotted)
        self._signal.cleared.connect(on_cleared)

    @QtCore.Slot(object)
    def __on_plotted(self, bounds):
        self._signal.plotted.emit(bounds)

    @QtCore.Slot()
    def __on_cleared(self):
        self._signal.plotted.emit()

    def get_file(self):
        return self._tempFile

    def set(self, telemetry=None):
        if telemetry is not None:
            self._telemetry = copy.copy(telemetry)
            if self._thread is not None and self._thread.isRunning():
                QtCore.QTimer.singleShot(0.5, self.set)
                return
            else:
                if len(telemetry) > 2:
                    self._thread = ThreadPlot(self,
                                              self._settings,
                                              self._telemetry,
                                              self._tempFile,
                                              self.__on_plotted)
                    self._thread.start()
                    return

        self._signal.cleared.emit()


class ThreadPlot(QtCore.QThread):
    def __init__(self, parent, settings, telemetry, tempFile, callback):
        QtCore.QThread.__init__(self, parent)
        self._settings = settings
        self._telemetry = telemetry
        self._tempFile = tempFile

        self._cancel = False

        self._signal = SignalPlot()
        self._signal.plotted.connect(callback)

    def __save(self, figure):
        try:
            self._tempFile.seek(0)
            plt.savefig(self._tempFile)
        except IOError:
            pass

        plt.close(figure)

    def run(self):
        figure = plt.figure(frameon=False)
        axes = figure.add_axes([0, 0, 1, 1])
        axes.set_axis_off()
        figure.patch.set_alpha(0)
        axes.axesPatch.set_alpha(0)

        xyz = zip(*self._telemetry)
        x = xyz[0]
        y = xyz[1]
        z = xyz[2]

        east = max(x)
        west = min(x)
        north = max(y)
        south = min(y)

        width = east - west
        height = north - south

        if width != 0 and height != 0:
            figure.set_size_inches((6, 6. * height / width))

            xi = numpy.linspace(west, east, IMAGE_SIZE)
            yi = numpy.linspace(south, north, IMAGE_SIZE)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                zi = mlab.griddata(x, y, z, xi=xi, yi=yi)
            axes.pcolormesh(xi, yi, zi, cmap=self._settings.heatmapColour)
            plt.axis([west, east, south, north], interp='linear')

        self.__save(figure)

        self._signal.plotted.emit((north, south, east, west))


class SignalPlot(QtCore.QObject):
    plotted = QtCore.Signal(object)
    cleared = QtCore.Signal()


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
