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


def build_harrier():
    filename = 'harrier-' + system + '-' + machine

    a = Analysis(['harrier.py'])    

    pyz = PYZ(a.pure)

    exe = EXE(pyz,
              a.scripts + [('O', '', 'OPTION')],
              a.binaries,
              a.zipfiles,
              a.datas,
              name=os.path.join('dist', filename),
              icon='wildfind.ico',
              upx=False)


def build_falconer():
    filename = 'falconer-' + system + '-' + machine
    hidden = ['PySide.QtXml', 'matplotlib.mlab.griddata.natgrid']

    a = Analysis(['falconer.py'],
                 hiddenimports=hidden)
    
    a.datas += Tree('wildfind/falconer/ui', prefix='wildfind/falconer/ui')
    a.datas += Tree('wildfind/falconer/htdocs', prefix='wildfind/falconer/htdocs')
    
    if system=='windows':
        a.datas += Tree('/openssl/', prefix='openssl')

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
machine = platform.machine().lower()

build_harrier()
build_falconer()
