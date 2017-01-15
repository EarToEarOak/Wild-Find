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
import sys

from PyInstaller.utils.win32 import versioninfo


def build_harrier(version):
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
              version=version,
              upx=False)


def build_falconer(version):
    filename = 'falconer-' + system + '-' + machine
    hidden = ['PySide.QtXml', 'matplotlib.mlab.griddata.natgrid']

    a = Analysis(['falconer.py'],
                 hiddenimports=hidden)

    a.datas += Tree('wildfind/falconer/gui', prefix='wildfind/falconer/gui')
    a.datas += Tree('wildfind/falconer/htdocs', prefix='wildfind/falconer/htdocs')

    if system == 'windows':
        a.datas += Tree('/openssl/', prefix='openssl')

    pyz = PYZ(a.pure)

    exe = EXE(pyz,
              a.scripts + [('O', '', 'OPTION')],
              a.binaries,
              a.zipfiles,
              a.datas,
              name=os.path.join('dist', filename),
              icon='wildfind.ico',
              version=version,
              upx=False)


def create_version():
    search = os.path.join(os.getcwd(), 'wildfind', 'common')
    sys.path.append(search)
    from version import VERSION
    version = VERSION
    version.append(0)

    ffi = versioninfo.FixedFileInfo(filevers=VERSION,
                                    prodvers=VERSION)

    strings = []
    strings.append(versioninfo.StringStruct('ProductName',
                                            'Wild Find'))
    strings.append(versioninfo.StringStruct('FileDescription',
                                            'Wildlif tracking'))
    strings.append(versioninfo.StringStruct('LegalCopyright',
                                            'Copyright 2012 - 2017 Al Brown'))
    table = versioninfo.StringTable('040904B0', strings)
    sInfo = versioninfo.StringFileInfo([table])
    var = versioninfo.VarStruct('Translation', [2057, 1200])
    vInfo = versioninfo.VarFileInfo([var])
    vvi = versioninfo.VSVersionInfo(ffi, [sInfo, vInfo])

    f = open('version.txt', 'w')
    f.write(vvi.__unicode__())
    f.close()

    print 'Version: {}.{}.{}.{}'.format (vvi.ffi.fileVersionMS >> 16,
                                         vvi.ffi.fileVersionMS & 0xffff,
                                         vvi.ffi.fileVersionLS >> 16,
                                         vvi.ffi.fileVersionLS & 0xFFFF)


system = platform.system().lower()
machine = platform.machine().lower()

version = None
if system == 'windows':
    create_version()
    version = 'version.txt'

build_harrier(version)
build_falconer(version)

if version is not None:
    os.remove('version.txt')
