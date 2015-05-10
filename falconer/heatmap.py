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

import copy
import tempfile

from PySide import QtCore
import matplotlib
matplotlib.use("Agg")
import numpy

import matplotlib.mlab as mlab
import matplotlib.pyplot as plt


IMAGE_SIZE = 300


class HeatMap(QtCore.QObject):
    def __init__(self, parent, callback):
        QtCore.QObject.__init__(self, parent)
        self._telemetry = None
        self._callback = callback

        self._thread = None
        self._tempFile = tempfile.TemporaryFile(suffix='.png')

        self._signal = SignalPlot()
        self._signal.plotted.connect(callback)

    @QtCore.Slot(object)
    def __on_plotted(self, bounds):
        self._thread = None
        self._signal.plotted.emit(bounds)

    def get_file(self):
        return self._tempFile

    def set(self, telemetry=None):
        if telemetry is not None:
            self._telemetry = copy.copy(telemetry)
            if self._thread is None:
                self._thread = ThreadPlot(self, self._telemetry,
                                          self._tempFile,
                                          self.__on_plotted)
                self._thread.start()
            else:
                QtCore.QTimer.singleShot(0.5, self.set)


class ThreadPlot(QtCore.QThread):
    def __init__(self, parent, telemetry, tempFile, callback):
        QtCore.QThread.__init__(self, parent)
        self._telemetry = telemetry
        self._tempFile = tempFile

        self._cancel = False

        self._signal = SignalPlot()
        self._signal.plotted.connect(callback)

    def run(self):
        xyz = zip(*self._telemetry)
        x = xyz[0]
        y = xyz[1]
        z = xyz[2]
        east = max(x)
        west = min(x)
        north = max(y)
        south = min(y)

        _figure, axes = plt.subplots()
        plt.axis('off')
        axes.set_aspect('equal')

        xi = numpy.linspace(west, east, IMAGE_SIZE)
        yi = numpy.linspace(south, north, IMAGE_SIZE)
        zi = mlab.griddata(x, y, z, xi=xi, yi=yi)
        axes.pcolormesh(xi, yi, zi)

        self._tempFile.seek(0)
        plt.savefig(self._tempFile, format='png', bbox_inches='tight')

        self._signal.plotted.emit((north, south, east, west))


class SignalPlot(QtCore.QObject):
    plotted = QtCore.Signal(object)


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
