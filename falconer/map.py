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


import json

from PySide import QtGui, QtWebKit, QtCore

from falconer import server, ui


class WidgetMap(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        url = 'http://localhost:{}/map.html'.format(server.PORT)
        webMap = QtWebKit.QWebView(self)
        webMap.load(QtCore.QUrl(url))
        frame = webMap.page().mainFrame()
        frame.setScrollBarPolicy(QtCore.Qt.Orientation.Horizontal,
                                 QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        frame.setScrollBarPolicy(QtCore.Qt.Orientation.Vertical,
                                 QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        controls = WidgetMapControls(self, webMap)

        layoutV = QtGui.QVBoxLayout()
        layoutV.addWidget(webMap)
        layoutV.addWidget(controls)

        self.setLayout(layoutV)


class WidgetMapControls(QtGui.QWidget):
    def __init__(self, parent, webMap):
        QtGui.QWidget.__init__(self, parent)

        self._parent = parent
        self._webMap = webMap
        self._track = True

        ui.loadUi(self, 'map_controls.ui')

        self._comboLayers.addItem('Waiting...')
        self._buttonTrack.setChecked(self._track)

        mapLink = MapLink(self)
        frame = self._webMap.page().mainFrame()
        frame.addToJavaScriptWindowObject('mapLink', mapLink)

    @QtCore.Slot(int)
    def on__comboLayers_activated(self, index):
        frame = self._webMap.page().mainFrame()
        frame.evaluateJavaScript('setLayer({});'.format(index))

    @QtCore.Slot(bool)
    def on__buttonTrack_clicked(self, checked):
        self._track = checked

    def update_comboLayers(self, names):
        self._comboLayers.clear()
        self._comboLayers.addItems(names)

        frame = self._webMap.page().mainFrame()
        layer = frame.evaluateJavaScript('getLayer();')
        self._comboLayers.setCurrentIndex(layer)

        self._comboLayers.setEnabled(True)
        self._buttonTrack.setEnabled(True)

    def cancel_track(self):
        self._track = False
        self._buttonTrack.setChecked(self._track)


class MapLink(QtCore.QObject):
    def __init__(self, parent):
        QtCore.QObject.__init__(self)
        self._parent = parent

    @QtCore.Slot()
    def on_interaction(self):
        self._parent.cancel_track()

    @QtCore.Slot(str)
    def layer_names(self, names):
        self._parent.update_comboLayers(json.loads(names))


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
