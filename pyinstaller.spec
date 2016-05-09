#!/usr/bin/env python
#
#
# Wild Find
#
#
# Copyright 2014 - 2016 Al Brown
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

import platform



def build_falconer():
    filename = 'falconer-' + system + '-' + architecture.lower()
    hidden = ['PySide.QtXml']

    a = Analysis(['falconer.py'],
                 hiddenimports=hidden)

    a.datas += Tree('falconer/ui', prefix='falconer/ui')
    a.datas += Tree('falconer/htdocs', prefix='falconer/htdocs')

    pyz = PYZ(a.pure)

    exe = EXE(pyz,
              a.scripts + [('O', '', 'OPTION')],
              a.binaries,
              a.zipfiles,
              a.datas,
              name=os.path.join('dist', filename),
              icon='wildfind.ico',
              upx=False)


system = platform.system().lower()
architecture, _null = platform.architecture()

build_falconer()
