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
import os
import sys
import tempfile
import zipfile


def get_program_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def add_program_path(*paths):
    cwd = get_program_path()
    return os.path.join(cwd, *paths)


def export_kml(fileName, image, telemetry):
    xyz = zip(*telemetry)
    north = max(xyz[1])
    south = min(xyz[1])
    east = max(xyz[0])
    west = min(xyz[0])

    keyhole = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
               '<GroundOverlay>\n'
               '\t<name>Wild Find</name>\n'
               '\t<Icon>\n'
               '\t\t<href>heatmap.png</href>\n'
               '\t\t<viewBoundScale>0.75</viewBoundScale>\n'
               '\t</Icon>\n'
               '\t<LatLonBox>\n'
               '\t\t<north>{north}</north>\n'
               '\t\t<south>{south}</south>\n'
               '\t\t<east>{east}</east>\n'
               '\t\t<west>{west}</west>\n'
               '\t</LatLonBox>\n'
               '</GroundOverlay>\n'
               '</kml>\n'
               ).format(north=north, south=south, east=east, west=west)

    fd, heatmap = tempfile.mkstemp()
    tempFile = os.fdopen(fd, 'wb')
    image.seek(0)
    tempFile.write(image.read())
    tempFile.close()

    fd, kml = tempfile.mkstemp()
    tempFile = os.fdopen(fd, 'w')
    tempFile.write(keyhole)
    tempFile.close()

    kmz = zipfile.ZipFile(fileName, 'w')
    kmz.write(heatmap, 'heatmap.png')
    kmz.write(kml, 'WildFind.kml')
    kmz.close()

    os.remove(heatmap)
    os.remove(kml)


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
