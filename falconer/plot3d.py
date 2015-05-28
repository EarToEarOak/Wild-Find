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

import matplotlib
import numpy
import warnings

matplotlib.rcParams['backend.qt4'] = 'PySide'
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.colorbar import ColorbarBase
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import ScalarFormatter, AutoMinorLocator
from matplotlib import mlab
from mpl_toolkits.mplot3d import Axes3D  # @UnusedImport

from PySide import QtGui, QtCore

from falconer import ui
from falconer.utils_qt import remove_context_help


class DialogPlot3d(QtGui.QDialog):
    def __init__(self, settings, telemetry):
        QtGui.QDialog.__init__(self, None)

        remove_context_help(self)

        self.customWidgets = {'WidgetPlot': WidgetPlot}

        ui.loadUi(self, 'plot3d.ui')

        self._widgetPlot.set(telemetry)
        self._widgetPlot.set_cmap(settings.heatmapColour)
        resolution = self._spinResolution.value()
        self._widgetPlot.set_resolution(resolution)
        self._widgetPlot.plot()

    @QtCore.Slot(bool)
    def on__checkWireframe_clicked(self, checked):
        self._widgetPlot.set_wireframe(checked)
        self._widgetPlot.plot()

    @QtCore.Slot(int)
    def on__spinResolution_valueChanged(self, value):
        self._widgetPlot.set_resolution(value)
        self._widgetPlot.plot()


class WidgetPlot(FigureCanvas):
    def __init__(self, parent=None):
        FigureCanvas.__init__(self, Figure(frameon=False))

        self._telemetry = None
        self._resolution = None
        self._cmap = None
        self._wireframe = False

        self.setParent(parent)

        self._figure = Figure(frameon=False)

        self._canvas = FigureCanvas(self._figure)
        self._canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self._canvas.setFocus()

        gs = GridSpec(1, 2, width_ratios=[9.5, 0.5])

        self._axes = self.figure.add_subplot(gs[0], projection='3d')
        self._axes.set_title('3D Plot')
        self._axes.set_xlabel('Longitude')
        self._axes.set_ylabel('Latitude')
        self._axes.set_zlabel('Level')
        self._axes.grid(True)
        formatMaj = ScalarFormatter(useOffset=False)
        self._axes.xaxis.set_major_formatter(formatMaj)
        self._axes.yaxis.set_major_formatter(formatMaj)
        self._axes.zaxis.set_major_formatter(formatMaj)
        formatMinor = AutoMinorLocator(10)
        self._axes.xaxis.set_minor_locator(formatMinor)
        self._axes.yaxis.set_minor_locator(formatMinor)
        self._axes.zaxis.set_minor_locator(formatMinor)

        self._axesBar = self.figure.add_subplot(gs[1])
        self._bar = ColorbarBase(self._axesBar)

        if matplotlib.__version__ >= '1.2':
            self.figure.tight_layout()

    def set(self, telemetry):
        self._telemetry = telemetry

    def set_cmap(self, cmap):
        self._cmap = cmap

    def set_resolution(self, res):
        self._resolution = res

    def set_wireframe(self, wireframe):
        self._wireframe = wireframe

    def plot(self):
        self.clear()

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
            xi = numpy.linspace(west, east, self._resolution)
            yi = numpy.linspace(south, north, self._resolution)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                xSurf, ySurf = numpy.meshgrid(xi, yi)
                zSurf = mlab.griddata(x, y, z, xi=xi, yi=yi)

            vmin = numpy.min(zSurf)
            vmax = numpy.max(zSurf)
            zSurf[numpy.where(numpy.ma.getmask(zSurf) == True)] = vmin
            zSurf.mask = False

            if self._wireframe:
                self._axes.plot_wireframe(xSurf, ySurf, zSurf,
                                          linewidth=0.5,
                                          gid='plot')
                self._axesBar.set_visible(False)
            else:
                self._axes.plot_surface(xSurf, ySurf, zSurf,
                                        vmin=vmin, vmax=vmax,
                                        rstride=1, cstride=1,
                                        linewidth=0.1,
                                        cmap=self._cmap,
                                        gid='plot')
                self._bar.set_cmap(self._cmap)
                self._bar.set_clim(vmin, vmax)
                self._axesBar.set_ylim(vmin, vmax)
                self._axesBar.set_visible(True)

        self.draw()

    def clear(self):
        children = self._axes.get_children()
        for child in children:
            gid = child.get_gid()
            if gid is not None and gid == 'plot':
                child.remove()


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
