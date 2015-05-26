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


import json

from PySide import QtGui, QtWebKit, QtCore, QtNetwork
from matplotlib import cm

from falconer import server, ui
from falconer.utils import add_program_path
from falconer.utils_qt import DialogPopup


RETRY_TIME = 2000
RETRIES = 5


class WidgetMap(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self._signal = SignalMap()
        self._popup = None

        url = 'http://localhost:{}/map.html'.format(server.PORT)
        self._url = QtCore.QUrl(url)
        self._retries = RETRIES

        self._labelLoad = QtGui.QLabel()
        self._labelLoad.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                      QtGui.QSizePolicy.Expanding)
        self._labelLoad.setAlignment(QtCore.Qt.AlignCenter)
        anim = add_program_path('falconer/ui/loader.gif')
        movie = QtGui.QMovie(anim)
        self._labelLoad.setMovie(movie)
        movie.start()

        self._webMap = QtWebKit.QWebView(self)
        self._webMap.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self._webMap.setAcceptDrops(False)
        self._webMap.setVisible(False)
        self._webMap.loadFinished.connect(self.__on_load_finished)
        self._webMap.linkClicked.connect(self.__on_link_clicked)

        page = self._webMap.page()
        page.setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateExternalLinks)
        manager = page.networkAccessManager()
        manager.finished[QtNetwork.QNetworkReply].connect(self.__loaded)

        settings = page.settings()
        settings.setAttribute(QtWebKit.QWebSettings.DeveloperExtrasEnabled,
                              True)

        self._inspector = QtWebKit.QWebInspector(self)
        self._inspector.setPage(page)
        self._inspector.setVisible(False)
        shortcut = QtGui.QShortcut(self)
        shortcut.setKey(QtGui.QKeySequence(QtCore.Qt.Key_F12))
        shortcut.activated.connect(self.__on_inspector)

        frame = self._webMap.page().mainFrame()
        frame.setScrollBarPolicy(QtCore.Qt.Orientation.Horizontal,
                                 QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        frame.setScrollBarPolicy(QtCore.Qt.Orientation.Vertical,
                                 QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._controls = WidgetMapControls(self, self._webMap)

        splitter = QtGui.QSplitter(self)
        splitter.setOrientation(QtCore.Qt.Vertical)
        splitter.addWidget(self._labelLoad)
        splitter.addWidget(self._webMap)
        splitter.addWidget(self._inspector)

        layoutV = QtGui.QVBoxLayout()
        layoutV.addWidget(splitter)
        layoutV.addWidget(self._controls)

        self.setLayout(layoutV)

        self._webMap.load(self._url)

    def __on_load_finished(self, _loaded):
        self._labelLoad.setVisible(False)
        self._webMap.setVisible(True)

    def __on_link_clicked(self, url):
        if self._popup is None:
            self._popup = DialogPopup()
            self._popup.rejected.connect(self.__on_close_popup)
            self._popup.show()

        self._popup.load(url)
        self._popup.raise_()

    def __loaded(self, reply):
        if reply.error() != QtNetwork.QNetworkReply.NoError:
            if self._retries:
                self._retries -= 1
                QtCore.QTimer.singleShot(RETRY_TIME, self.__on_retry)
            else:
                self._webMap.setHtml('Could not load map')

    def __on_inspector(self):
        self._inspector.setVisible(not self._inspector.isVisible())

    def __on_retry(self):
        self._webMap.load(self._url)

    def __on_close_popup(self):
        self._popup = None

    def on_interaction(self,):
        self._controls.cancel_track()

    def on_layer_names(self, layers):
        self._controls.update_layers(json.loads(layers))

    def on_map_loaded(self):
        self._signal.loaded.emit()

    def on_colour(self):
        self._signal.colour.emit()

    def on_selected(self, selected):
        sels = [float(f) for f in json.loads(selected)]
        self._signal.selected.emit(sels)

    def resizeEvent(self, _event):
        self._controls.follow()

    def connect(self, loaded, colour, selected):
        self._signal.loaded.connect(loaded)
        self._signal.colour.connect(colour)
        self._signal.selected.connect(selected)

    def transform_coords(self, xyz):
        return self._controls.transform_coords(xyz)

    def show_busy(self, show):
        self._controls.show_busy(show)

    def get_pos(self):
        return self._controls.get_pos()

    def get_map(self):
        page = self._webMap.page()
        frame = page.mainFrame()

        size = page.viewportSize()
        image = QtGui.QImage(size, QtGui.QImage.Format_ARGB32)
        painter = QtGui.QPainter(image)
        frame.render(painter, QtWebKit.QWebFrame.ContentsLayer)
        painter.end()

        return image

    def set_settings(self, settings):
        self._controls.set_settings(settings)

    def set_units(self, units):
        self._controls.set_units(units)

    def set_pos(self, pos, zoom):
        self._controls.set_pos(pos, zoom)

    def set_locations(self, locations):
        self.clear_locations()
        self._controls.set_locations(locations)

    def set_heatmap(self, bounds):
        self._controls.set_heatmap(bounds)

    def select_locations(self, frequencies):
        self._controls.select_locations(frequencies)

    def clear_locations(self):
        self._controls.clear_locations()

    def clear_heatmap(self):
        self._controls.clear_heatmap()


class WidgetMapControls(QtGui.QWidget):
    def __init__(self, parent, webMap):
        QtGui.QWidget.__init__(self, parent)

        self._webMap = webMap

        self._settings = None
        self._follow = True

        self._signal = SignalMap()
        self._signal.colour.connect(parent.on_colour)

        ui.loadUi(self, 'map_controls.ui')

        self._comboLayers.addItem('Waiting...')
        colours = [colour for colour in cm.cmap_d]
        colours.sort()
        self._comboColour.addItems(colours)

        frame = self._webMap.page().mainFrame()
        self._mapLink = MapLink(frame)
        self._mapLink.connect(parent.on_interaction,
                              parent.on_layer_names,
                              parent.on_map_loaded,
                              parent.on_colour,
                              parent.on_selected)
        frame.addToJavaScriptWindowObject('mapLink', self._mapLink)

    @QtCore.Slot(int)
    def on__comboLayers_activated(self, index):
        self._mapLink.set_layer(index)

    @QtCore.Slot(bool)
    def on__checkLocations_clicked(self, checked):
        self._mapLink.show_locations(checked)
        self.follow()

    @QtCore.Slot(bool)
    def on__checkTrack_clicked(self, checked):
        self._mapLink.show_track(checked)

    @QtCore.Slot(bool)
    def on__checkHeatmap_clicked(self, checked):
        self._mapLink.show_heatmap(checked)

    @QtCore.Slot(int)
    def on__sliderOpacity_valueChanged(self, opacity):
        self._mapLink.set_heatmap_opacity(opacity)

    @QtCore.Slot(int)
    def on__comboColour_activated(self, index):
        colours = [colour for colour in cm.cmap_d]
        colours.sort()
        colour = colours[index]
        self._settings.heatmapColour = colour

        self._signal.colour.emit()

    @QtCore.Slot(bool)
    def on__checkFollow_clicked(self, checked):
        self._follow = checked
        self.follow()

    def follow(self):
        if self._follow:
            self._mapLink.follow()

    def show_busy(self, show):
        self._mapLink.show_busy(show)

    def update_layers(self, names):
        self._comboLayers.clear()
        self._comboLayers.addItems(names)

        layer = self._mapLink.get_layer()
        self._comboLayers.setCurrentIndex(layer)

        self.setEnabled(True)

    def cancel_track(self):
        self._follow = False
        self._checkFollow.setChecked(self._follow)

    def transform_coords(self, xyz):
        return self._mapLink.transform_coords(xyz)

    def get_pos(self):
        return self._mapLink.get_pos()

    def set_settings(self, settings):
        self._settings = settings
        colours = [colour for colour in cm.cmap_d]
        colours.sort()
        index = colours.index(settings.heatmapColour)
        self._comboColour.setCurrentIndex(index)

    def set_units(self, units):
        self._mapLink.set_units(units)

    def set_pos(self, pos, zoom):
        self._mapLink.set_pos(pos, zoom)

    def set_locations(self, locations):
        self._mapLink.set_locations(locations)
        self.follow()

    def set_heatmap(self, bounds):
        self._mapLink.set_heatmap(bounds)

    def select_locations(self, frequencies):
        self._mapLink.select_locations(frequencies)

    def clear_locations(self):
        self._follow = True
        self._checkFollow.setChecked(self._follow)
        self._mapLink.clear_locations()

    def clear_heatmap(self):
        self._mapLink.clear_heatmap()



class MapLink(QtCore.QObject):
    def __init__(self, frame):
        QtCore.QObject.__init__(self)
        self._frame = frame

        self._signal = SignalMap()

    def __exec_js(self, js):
        return self._frame.evaluateJavaScript(js)

    def __bool_to_js(self, value):
        return '{}'.format(value).lower()

    @QtCore.Slot()
    def on_interaction(self):
        self._signal.interaction.emit()

    @QtCore.Slot(str)
    def on_layer_names(self, names):
        self._signal.layers.emit(names)
        self._signal.loaded.emit()

    @QtCore.Slot(str)
    def on_selected(self, frequencies):
        self._signal.selected.emit(frequencies)

    def connect(self, interaction, layer, loaded, colour, selected):
        self._signal.interaction.connect(interaction)
        self._signal.layers.connect(layer)
        self._signal.loaded.connect(loaded)
        self._signal.colour.connect(colour)
        self._signal.selected.connect(selected)

    def get_layer(self):
        js = 'getLayer();'
        return self.__exec_js(js)

    def get_pos(self):
        js = 'getPos();'
        return self.__exec_js(js)

    def set_layer(self, layer):
        js = 'setLayer({});'.format(layer)
        self.__exec_js(js)

    def set_units(self, units):
        js = 'setUnits("{}");'.format(units.lower())
        self.__exec_js(js)

    def set_locations(self, locations):
        for location in locations:
            js = ('addLocation('
                  '"{:.99g}", "{:3.1f}", "{:2.1f}",'
                  '{}, {});').format(*location)
            self.__exec_js(js)

    def set_heatmap_opacity(self, opacity):
        js = 'setHeatmapOpacity({});'.format(opacity / 100.)
        self.__exec_js(js)

    def set_heatmap(self, bounds):
        js = 'setHeatmap({}, {}, {}, {});'.format(*bounds)
        self.__exec_js(js)

    def set_pos(self, pos, zoom):
        js = 'setPos({}, {}, {});'.format(pos[0], pos[1], zoom)
        self.__exec_js(js)

    def select_locations(self, signals):
        for signal in signals:
            freq = signal[0]
            selected = self.__bool_to_js(signal[1])
            js = 'selectLocation("{:.99g}", {})'.format(freq,
                                                        selected)
            self.__exec_js(js)

    def clear_locations(self):
        js = 'clearLocations();'
        self.__exec_js(js)

    def clear_heatmap(self):
        js = 'clearHeatmap();'
        self.__exec_js(js)

    def show_locations(self, show):
        js = 'showLocations({});'.format(self.__bool_to_js(show))
        self.__exec_js(js)

    def show_track(self, show):
        js = 'showTrack({});'.format(self.__bool_to_js(show))
        self.__exec_js(js)

    def show_heatmap(self, show):
        js = 'showHeatmap({});'.format(self.__bool_to_js(show))
        self.__exec_js(js)

    def show_busy(self, show):
        js = 'showBusy({});'.format(self.__bool_to_js(show))
        self.__exec_js(js)

    def follow(self):
        js = 'follow();'
        self.__exec_js(js)

    def transform_coords(self, coords):
        transformed = []
        for coord in coords:
            js = 'transformCoord({}, {});'.format(coord[0], coord[1])
            trans = self.__exec_js(js)
            trans.extend([coord[2]])
            transformed.append(trans)

        return transformed


class SignalMap(QtCore.QObject):
    interaction = QtCore.Signal()
    layers = QtCore.Signal(list)
    loaded = QtCore.Signal()
    colour = QtCore.Signal()
    selected = QtCore.Signal(list)


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
