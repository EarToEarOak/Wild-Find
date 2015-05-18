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

from falconer import ui
from falconer.utils_qt import TableSelectionMenu
import matplotlib.pyplot as plt


class WidgetSignals(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        ui.loadUi(self, 'signals.ui')

        self._signal = SignalSignals()

        self._model = ModelSignals()
        self._proxyModel = QtGui.QSortFilterProxyModel(self)
        self._proxyModel.setDynamicSortFilter(True)
        self._proxyModel.setSourceModel(self._model)

        self._tableSignals.setModel(self._proxyModel)
        self._tableSignals.resizeColumnsToContents()

        selection = self._tableSignals.selectionModel()
        selection.selectionChanged.connect(self.__on_signal_select)

        self._contextMenu = TableSelectionMenu(self._tableSignals,
                                               self._model,
                                               True)

        header = self._tableSignals.horizontalHeader()
        header.setResizeMode(QtGui.QHeaderView.Fixed)

        self.__set_width()

        palette = self.palette()
        colour = palette.color(QtGui.QPalette.Active, QtGui.QPalette.Highlight)
        palette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Highlight,
                         colour)
        self.setPalette(palette)

    def __set_width(self):
        margins = self.layout().contentsMargins()
        width = self._tableSignals.verticalHeader().width()
        width += self._tableSignals.horizontalHeader().length()
        width += self._tableSignals.style().pixelMetric(QtGui.QStyle.PM_ScrollBarExtent)
        width += self._tableSignals.frameWidth() * 2
        width += margins.left() + margins.right()
        width += self.layout().spacing()
        self.setMaximumWidth(width)

    @QtCore.Slot(QtGui.QItemSelection, QtGui.QItemSelection)
    def __on_signal_select(self, selected, deselected):
        selection = []

        selected = selected.indexes()
        deslected = deselected.indexes()
        self.__append_selection(selection, selected, True)
        self.__append_selection(selection, deslected, False)

        self._signal.select.emit(selection)

    @QtCore.Slot(bool)
    def on__buttonHistogram_clicked(self, _clicked):
        dlg = DialogHistogram(self, self._model.get_all())
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

    def set(self, signals):
        self._model.set(signals)
        self._tableSignals.resizeColumnsToContents()
        self.__set_width()

        self._tableSignals.setEnabled(True)
        self._buttonHistogram.setEnabled(True)

    def get(self):
        return self._model.get()

    def get_filters(self):
        return self._model.get_filters()

    def set_filtered(self, filtered):
        self._model.set_filtered(filtered)

    def get_filtered(self):
        return self._model.get_filtered()

    def clear(self):
        self._model.set([])
        self._model.set_filtered([])
        self._tableSignals.setEnabled(False)
        self._buttonHistogram.setEnabled(False)


class ModelSignals(QtCore.QAbstractTableModel):
    HEADER = [None, 'Freq', 'Rate', 'Seen']
    HEADER_TIPS = ['Included', 'Signal frequency (MHz)',
                   'Pulse rate (PPM)', 'Total detections']

    def __init__(self):
        QtCore.QAbstractTableModel.__init__(self)

        self._signal = SignalSignals()
        self._signals = []
        self._filtered = []

    def rowCount(self, _parent=None):
        return len(self._signals)

    def columnCount(self, _parent=None):
        return len(self.HEADER)

    def headerData(self, col, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.HEADER[col]
        elif role == QtCore.Qt.ToolTipRole:
            return self.HEADER_TIPS[col]

        return None

    def data(self, index, role):
        value = self._signals[index.row()][index.column()]
        data = None

        if role == QtCore.Qt.DisplayRole:
            if index.column() == 1:
                data = '{:8.4f}'.format(value / 1e6)
            elif index.column() == 2:
                data = '{:5.1f}'.format(value)
            elif index.column() != 0:
                data = value
        elif role == QtCore.Qt.CheckStateRole:
            if index.column() == 0:
                data = value

        return data

    def setData(self, index, value, role):
        if role == QtCore.Qt.CheckStateRole:
            self._signals[index.row()][index.column()] = value
            frequency = self._signals[index.row()][1]
            checked = value == QtCore.Qt.Checked
            if checked:
                self._filtered.remove(frequency)
            else:
                self._filtered.append(frequency)

            self._signal.filter.emit()
            return True

        return False

    def flags(self, index):
        flags = QtCore.Qt.ItemIsEnabled
        if index.column() == 0:
            flags |= (QtCore.Qt.ItemIsEditable |
                      QtCore.Qt.ItemIsUserCheckable)
        elif index.column() == 1:
            flags |= QtCore.Qt.ItemIsSelectable

        return flags

    def connect(self, on_filter):
        self._signal.filter.connect(on_filter)

    def set(self, signals):
        self.beginResetModel()
        del self._signals[:]
        for frequency, rate, count in signals:
            checked = QtCore.Qt.Checked
            if frequency in self._filtered:
                checked = QtCore.Qt.Unchecked
            self._signals.append([checked, frequency, rate, count])
        self.endResetModel()

    def get(self):
        frequencies = [frequency for _check, frequency,
                       _rate, _freq in self._signals]
        return frequencies

    def get_all(self):
        return self._signals

    def get_filtered(self):
        return self._filtered

    def set_filtered(self, filtered):
        self.beginResetModel()
        self._filtered = filtered
        for i in range(len(self._signals)):
            signal = self._signals[i]
            if signal[1] in filtered:
                signal[0] = QtCore.Qt.Unchecked
            else:
                signal[0] = QtCore.Qt.Checked

        self.endResetModel()

        self._signal.filter.emit()


class DialogHistogram(QtGui.QDialog):
    def __init__(self, parent, signals):
        QtGui.QDialog.__init__(self, parent)

        self._signals = signals
        self._scale = 1.
        self._dragStart = None

        ui.loadUi(self, 'signals_hist.ui')
        self.setWindowFlags(QtCore.Qt.Tool)

        self._graphicsView.viewport().installEventFilter(self)

        size = self._buttonIn.size()
        size.setHeight(size.height() / 1.5)
        size.setWidth(size.height())
        self._buttonIn.setMaximumSize(size)
        self._buttonOut.setMaximumSize(size)

        self.activateWindow()

    @QtCore.Slot(bool)
    def on__buttonIn_clicked(self, _clicked):
        pos = self.__get_centre()
        self.__zoom(pos, 120)

    @QtCore.Slot(bool)
    def on__buttonOut_clicked(self, _clicked):
        pos = self.__get_centre()
        self.__zoom(pos, -120)

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

        formatter = ScalarFormatter(useOffset=False)
        axes.xaxis.set_major_formatter(formatter)
        axes.yaxis.set_major_formatter(formatter)

        _, x, y = zip(*self._signals)
        x = [freq / 1e6 for freq in x]
        width = min(numpy.diff(x))
        bars = axes.bar(x, y, width=width, color='blue')
        for i in range(len(y)):
            bar = bars[i]
            freq = x[i]
            height = bar.get_height()
            text = axes.text(bar.get_x() + width / 2.,
                             height,
                             '{:.4f}'.format(freq),
                             rotation=45,
                             ha='center', va='bottom', size='smaller')
            if matplotlib.__version__ >= '1.3':
                effect = patheffects.withStroke(linewidth=2,
                                                foreground="w",
                                                alpha=0.75)
                text.set_path_effects([effect])

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
