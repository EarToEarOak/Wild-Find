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
        webMap = QtWebKit.QWebView()
        webMap.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        webMap.load(QtCore.QUrl(url))

        page = webMap.page()
        settings = page.settings()
        settings.setAttribute(QtWebKit.QWebSettings.DeveloperExtrasEnabled,
                              True)
        self._inspector = QtWebKit.QWebInspector(self)
        self._inspector.setPage(page)
        self._inspector.setVisible(False)
        shortcut = QtGui.QShortcut(self)
        shortcut.setKey(QtGui.QKeySequence(QtCore.Qt.Key_F12))
        shortcut.activated.connect(self.__on_inspector)

        frame = webMap.page().mainFrame()
        frame.setScrollBarPolicy(QtCore.Qt.Orientation.Horizontal,
                                 QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        frame.setScrollBarPolicy(QtCore.Qt.Orientation.Vertical,
                                 QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._controls = WidgetMapControls(self, webMap)

        splitter = QtGui.QSplitter(self)
        splitter.setOrientation(QtCore.Qt.Vertical)
        splitter.addWidget(webMap)
        splitter.addWidget(self._inspector)

        layoutV = QtGui.QVBoxLayout()
        layoutV.addWidget(splitter)
        layoutV.addWidget(self._controls)

        self.setLayout(layoutV)

    @QtCore.Slot()
    def __on_inspector(self):
        self._inspector.setVisible(not self._inspector.isVisible())

    def set_locations(self, locations):
        self.clear()
        self._controls.set_locations(locations)

    def clear(self):
        self._controls.clear()


class WidgetMapControls(QtGui.QWidget):
    def __init__(self, parent, webMap):
        QtGui.QWidget.__init__(self, parent)

        self._parent = parent
        self._webMap = webMap

        self._follow = True

        ui.loadUi(self, 'map_controls.ui')

        self._comboLayers.addItem('Waiting...')

        frame = self._webMap.page().mainFrame()
        self._mapLink = MapLink(self, frame)
        frame.addToJavaScriptWindowObject('mapLink', self._mapLink)

    @QtCore.Slot(int)
    def on__comboLayers_activated(self, index):
        self._mapLink.set_layer(index)

    @QtCore.Slot(bool)
    def on__checkFollow_clicked(self, checked):
        self._follow = checked
        self.__follow()

    @QtCore.Slot(bool)
    def on__checkLocations_clicked(self, checked):
        self._mapLink.show_locations(checked)
        self.__follow()

    @QtCore.Slot(bool)
    def on__checkHeatmap_clicked(self, checked):
        pass

    def __follow(self):
        if self._follow:
            self._mapLink.follow()

    def update_layers(self, names):
        self._comboLayers.clear()
        self._comboLayers.addItems(names)

        layer = self._mapLink.get_layer()
        self._comboLayers.setCurrentIndex(layer)

        self.setEnabled(True)

    def cancel_track(self):
        self._follow = False
        self._checkFollow.setChecked(self._follow)

    def set_locations(self, locations):
        self._mapLink.set_locations(locations)
        self.__follow()

    def clear(self):
        self._follow = True
        self._checkFollow.setChecked(self._follow)
        self._mapLink.clear()


class MapLink(QtCore.QObject):
    def __init__(self, parent, frame):
        QtCore.QObject.__init__(self)
        self._parent = parent
        self._frame = frame

    def __exec_js(self, js):
        return self._frame.evaluateJavaScript(js)

    @QtCore.Slot()
    def on_interaction(self):
        self._parent.cancel_track()

    @QtCore.Slot(str)
    def on_layer_names(self, names):
        self._parent.update_layers(json.loads(names))

    def get_layer(self):
        js = 'getLayer();'
        return self.__exec_js(js)

    def set_layer(self, layer):
        js = 'setLayer({});'.format(layer)
        self.__exec_js(js)

    def set_locations(self, locations):
        for location in locations:
            js = 'addLocations({},{});'.format(location[0], location[1])
            self.__exec_js(js)

    def show_locations(self, show):
        js = 'showLocations({});'.format('{}'.format(show).lower())
        self.__exec_js(js)

    def follow(self):
        js = 'follow();'
        self.__exec_js(js)

    def clear(self):
        js = 'clearLocations();'
        self.__exec_js(js)


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
