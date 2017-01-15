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

from PySide import QtGui

from wildfind.falconer import ui
from wildfind.falconer.utils import get_resource_ui
from wildfind.falconer.utils_qt import win_remove_context_help
from wildfind.common.version import VERSION


class DialogAbout(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)

        ui.loadUi(self, 'about.ui')
        win_remove_context_help(self)

        pixmap = QtGui.QPixmap(get_resource_ui('logo.png'))
        self._labelLogo.setPixmap(pixmap)

        self._version.setText('v' + '.'.join([str(x) for x in VERSION]))


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
