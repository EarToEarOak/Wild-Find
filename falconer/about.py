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

from falconer import ui
from falconer.utils import add_program_path
from falconer.utils_qt import remove_context_help


class DialogAbout(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)

        remove_context_help(self)

        ui.loadUi(self, 'about.ui')

        pixmap = QtGui.QPixmap(add_program_path('falconer',
                                                'ui',
                                                'logo.png'))
        self._labelLogo.setPixmap(pixmap)


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
