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


from PySide import QtGui, QtCore
from matplotlib import patheffects
import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.ticker import ScalarFormatter
import numpy

from wildfind.falconer import ui
from wildfind.falconer.table import format_freq, format_rate, Model
from wildfind.falconer.utils_qt import TableSelectionMenu, win_set_maximise, win_set_icon
import matplotlib.pyplot as plt


class WidgetSignals(QtGui.QWidget):
    HEADER = [None, 'Freq', 'Rate', 'Seen']
    HEADER_TIPS = ['Included', 'Signal frequency (MHz)',
                   'Rate (PPM)', 'Total detections']

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        ui.loadUi(self, 'signals.ui')

        self._signal = SignalSignals()

        formatters = [None, format_freq, format_rate, None]
        self._model = Model(self._signal, self.HEADER, self.HEADER_TIPS,
                            formatters, 1)
        self._proxyModel = QtGui.QSortFilterProxyModel(self)
        self._proxyModel.setDynamicSortFilter(True)
        self._proxyModel.setSourceModel(self._model)

        self._tableSignals.setModel(self._proxyModel)

        selection = self._tableSignals.selectionModel()
        selection.selectionChanged.connect(self.__on_signal_select)

        self._contextMenu = TableSelectionMenu(self._tableSignals,
                                               self._model,
                                               self.hasSelection)

        self.__set_width()

        palette = self.palette()
        colour = palette.color(QtGui.QPalette.Active, QtGui.QPalette.Highlight)
        palette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Highlight,
                         colour)
        self.setPalette(palette)

    def __set_width(self):
        self._tableSignals.resizeColumnsToContents()

        margins = self.layout().contentsMargins()
        width = self._tableSignals.verticalHeader().width()
        width += self._tableSignals.horizontalHeader().length()
        width += self._tableSignals.style().pixelMetric(QtGui.QStyle.PM_ScrollBarExtent)
        width += self._tableSignals.frameWidth() * 2
        width += margins.left() + margins.right()
        width += self.layout().spacing()
        self.setMaximumWidth(width)

    def __on_signal_select(self, selected, deselected):
        selection = []

        selected = selected.indexes()
        deslected = deselected.indexes()
        self.__append_selection(selection, selected, True)
        self.__append_selection(selection, deslected, False)

        self._signal.select.emit(selection)

    @QtCore.Slot(bool)
    def on__buttonHistogram_clicked(self, _clicked):
        dlg = DialogHistogram(self._model.get_all(),
                              self._model.get_filtered())
        dlg.exec_()

    def __append_selection(self, selection, select, selected):
        signals = self._model.get()
        for index in select:
            data = index.data()
            if data is not None and index.column() == 1:
                mapped = self._proxyModel.mapToSource(index)
                freq = signals[mapped.row()]
                selection.append((freq, selected))

    def connect(self, on_filter, on_selected):
        self._model.connect(on_filter)
        self._signal.select.connect(on_selected)

    def select(self, frequencies):
        freqs = ['{:.4f}'.format(f / 1e6) for f in frequencies]

        scroll = None
        self._tableSignals.clearSelection()
        for i in range(self._model.rowCount()):
            index = self._model.index(i, 1)
            if index.data() in freqs:
                mapped = self._proxyModel.mapFromSource(index)
                self._tableSignals.selectRow(mapped.row())
                if scroll is None:
                    scroll = mapped

        if scroll is not None:
            self._tableSignals.scrollTo(mapped)

    def hasSelection(self):
        return self._tableSignals.selectionModel().hasSelection()

    def set(self, signals):
        self._model.set(signals)
        self.__set_width()

        self._tableSignals.setEnabled(True)
        self._buttonHistogram.setEnabled(True)

    def set_font(self, font):
        newFont = QtGui.QFont()
        newFont.fromString(font)
        self._tableSignals.setFont(newFont)
        self.__set_width()

    def get(self):
        return self._model.get()

    def get_filters(self):
        return self._model.get_filters()

    def get_filtered(self):
        return self._model.get_filtered()

    def clear(self):
        self._model.set([])
        self._model.set_filtered([], False)
        self._tableSignals.setEnabled(False)
        self._buttonHistogram.setEnabled(False)


class DialogHistogram(QtGui.QDialog):
    def __init__(self, signals, filtered):
        QtGui.QDialog.__init__(self)

        self._signals = signals
        self._filtered = filtered
        self._scale = 1.
        self._dragStart = None

        ui.loadUi(self, 'signals_hist.ui')
        win_set_icon(self)
        win_set_maximise(self)

        self._graphicsView.viewport().installEventFilter(self)

        size = self._buttonIn.size()
        size.setHeight(size.height() / 1.5)
        size.setWidth(size.height())
        self._buttonIn.setMaximumSize(size)
        self._buttonOut.setMaximumSize(size)

        self._show_all = self._checkAll.isChecked()
        if not len(filtered):
            self._checkAll.setEnabled(False)

        self.activateWindow()

    @QtCore.Slot(bool)
    def on__buttonIn_clicked(self, _clicked):
        pos = self.__get_centre()
        self.__zoom(pos, 120)

    @QtCore.Slot(bool)
    def on__buttonOut_clicked(self, _clicked):
        pos = self.__get_centre()
        self.__zoom(pos, -120)

    @QtCore.Slot(bool)
    def on__checkAll_clicked(self, checked):
        self._show_all = checked
        self.__plot()

    @QtCore.Slot()
    def on__buttonBox_rejected(self):
        self.reject()

    def resizeEvent(self, _event):
        self.__plot()

    def eventFilter(self, obj, event):
        if event.type() is QtCore.QEvent.Wheel:
            delta = event.delta()
            self.__zoom(event.pos(), delta)
            return True

        return QtGui.QDialog.eventFilter(self, obj, event)

    def __get_centre(self):
        rect = self._graphicsView.rect()
        return rect.center()

    def __zoom(self, pos, delta):
        scaleOld = self._scale
        scale = self._scale + delta / 1000.
        if scale < 1:
            scale = 1.
        elif scale > 5:
            scale = 5.

        if scale != scaleOld:
            self._scale = scale
            self.__plot(pos)

    def __plot(self, mousePos=None):
        figure, axes = plt.subplots()
        dpi = figure.get_dpi()
        viewSize = self._graphicsView.size()
        scrollSize = self._graphicsView.style().pixelMetric(QtGui.QStyle.PM_ScrollBarExtent)
        size = QtCore.QSize(viewSize.width() * self._scale - scrollSize,
                            viewSize.height() * self._scale - scrollSize)

        figure.set_size_inches(size.width() / float(dpi),
                               size.height() / float(dpi))
        figure.patch.set_facecolor('w')
        plt.title('Signals')
        plt.xlabel('Frequency (MHz)')
        plt.ylabel('Detections')
        plt.grid(True)

        if matplotlib.__version__ >= '1.2':
            figure.tight_layout()

        renderer = plt.gcf().canvas.get_renderer()

        formatter = ScalarFormatter(useOffset=False)
        axes.xaxis.set_major_formatter(formatter)
        axes.yaxis.set_major_formatter(formatter)

        if self._show_all:
            signals = self._signals
        else:
            signals = [signal for signal in self._signals
                       if signal[0] not in self._filtered]

        x, z, y = zip(*signals)
        x = [freq / 1e6 for freq in x]
        if len(x) > 2:
            width = min(numpy.diff(x)) / 2.
        else:
            width = 20 / 1e6

        bars = axes.bar(x, y, width=width, color='blue')

        xmin, xmax = plt.xlim()
        ymin, ymax = plt.ylim()

        for i in range(len(y)):
            bar = bars[i]
            freq = x[i]
            rate = z[i]
            height = bar.get_height()
            text = axes.text(bar.get_x() + width / 2.,
                             height,
                             '{:.4f} ({:.1f})'.format(freq, rate),
                             rotation=45,
                             ha='left', va='bottom', size='smaller')
            if matplotlib.__version__ >= '1.3':
                effect = patheffects.withStroke(linewidth=2,
                                                foreground="w",
                                                alpha=0.75)
                text.set_path_effects([effect])

                bounds = text.get_window_extent(renderer)
                bounds = bounds.transformed(axes.transData.inverted())
                extents = bounds.extents
                xmin = min(xmin, extents[0])
                ymin = min(ymin, extents[1])
                xmax = max(xmax, extents[2])
                ymax = max(ymax, extents[3])

        plt.xlim(xmin, xmax)
        plt.ylim(ymin, ymax)

        canvas = FigureCanvasAgg(figure)
        canvas.draw()
        renderer = canvas.get_renderer()
        if matplotlib.__version__ >= '1.2':
            rgba = renderer.buffer_rgba()
        else:
            rgba = renderer.buffer_rgba(0, 0)

        image = QtGui.QImage(rgba, size.width(), size.height(),
                             QtGui.QImage.Format_ARGB32)
        pixmap = QtGui.QPixmap.fromImage(image)
        scene = QtGui.QGraphicsScene(self)
        scene.addPixmap(pixmap)
        scene.setSceneRect(image.rect())
        self._graphicsView.setScene(scene)

        if mousePos is not None:
            self._graphicsView.centerOn(mousePos.x() * self._scale,
                                        mousePos.y() * self._scale)

        plt.close()


class SignalSignals(QtCore.QObject):
    filter = QtCore.Signal()
    select = QtCore.Signal(list)


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
