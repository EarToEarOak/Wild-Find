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


def export_kml(fileName, locations, telemetry, image):
    points = ('    <Folder>\n'
              '      <name>Locations</name>\n')
    for location in locations:
        desc = ('{:.4f}MHz\n'
                '{:.1f}PPM\n'
                '{:.1f}dB').format(location[0] / 1e6,
                                   location[1],
                                   location[2])
        points += ('      <Placemark>\n'
                   '      <description>{}</description>\n'
                   '        <styleUrl>#location</styleUrl>\n'
                   '        <Point>\n'
                   '          <altitudeMode>clampToGround</altitudeMode>\n'
                   '        <coordinates>{},{},0</coordinates>\n'
                   '        </Point>\n'
                   '    </Placemark>\n').format(desc,
                                                location[3],
                                                location[4])
    points += '    </Folder>\n'

    coords = ''
    for coord in telemetry:
        coords += '{},{},0\n'.format(coord[0], coord[1])
    track = ('    <Placemark>\n'
             '      <name>Track</name>\n'
             '      <styleUrl>#track</styleUrl>\n'
             '      <LineString>\n'
             '        <altitudeMode>clampToGround</altitudeMode>\n'
             '        <coordinates>{coords}</coordinates>\n'
             '      </LineString>\n'
             '    </Placemark>\n').format(coords=coords)

    xyz = zip(*telemetry)
    north = max(xyz[1])
    south = min(xyz[1])
    east = max(xyz[0])
    west = min(xyz[0])

    keyhole = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
               '  <Document>\n'
               '    <Style id="track">\n'
               '      <LineStyle>\n'
               '        <width>3</width>\n'
               '        <color>ff0063dd</color>\n'
               '      </LineStyle>\n'
               '    </Style>\n'

               '    <Style id="location">\n'
               '      <IconStyle>\n'
               '        <Icon>\n'
               '          <href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href>'
               '        </Icon>\n'
               '        <color>ff0060ff</color>'
               '      </IconStyle>\n'
               '    </Style>\n'

               '    <name>Wild Find</name>\n'
               '    <GroundOverlay>\n'
               '      <name>Heatmap</name>\n'
               '      <Icon>\n'
               '        <href>heatmap.png</href>\n'
               '        <viewBoundScale>0.75</viewBoundScale>\n'
               '      </Icon>\n'
               '      <LatLonBox>\n'
               '        <north>{north}</north>\n'
               '        <south>{south}</south>\n'
               '        <east>{east}</east>\n'
               '        <west>{west}</west>\n'
               '      </LatLonBox>\n'
               '    </GroundOverlay>\n'

               '{points}'
               '{track}'

               '  </Document>\n'
               '</kml>\n'
               ).format(north=north, south=south, east=east, west=west,
                        points=points, track=track)

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


def unique_locations(xyz):
    locations = {}
    for x, y, z in xyz:
        if (x, y) in locations:
            locations[(x, y)] = max(locations[(x, y)], z)
        else:
            locations[(x, y)] = z

    x = []
    y = []
    z = []
    for coord in locations.iterkeys():
        x.append(coord[0])
        y.append(coord[1])
        z.append(locations[coord])

    return x, y, z


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
