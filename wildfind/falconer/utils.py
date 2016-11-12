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


# def get_program_path():
#     return os.path.dirname(os.path.realpath(sys.argv[0]))
#
#
# def add_program_path(*paths):
#     cwd = get_program_path()
#     return os.path.join(cwd, *paths)

def get_program_path():
    if getattr(sys, 'frozen', False):
        path = sys._MEIPASS
    else:
        path = os.path.dirname(os.path.realpath(sys.argv[0]))

    return path


def get_ui_path(filename):
    return os.path.join(get_program_path(), 'falconer', 'ui', filename)


def get_htdocs_path(filename):
    return os.path.join(get_program_path(), 'falconer', 'htdocs', filename)


def export_kml(fileName, telemetry, image):
    points = ('    <Folder>\n'
              '      <name>Locations</name>\n')
    for location in telemetry:
        desc = ('{:.4f}MHz\n'
                '{:.1f}PPM\n'
                '{:.1f}dB').format(location['Level'] / 1e6,
                                   location['Rate'],
                                   location['Level'])
        points += ('      <Placemark>\n'
                   '      <description>{}</description>\n'
                   '        <styleUrl>#location</styleUrl>\n'
                   '        <Point>\n'
                   '          <altitudeMode>clampToGround</altitudeMode>\n'
                   '        <coordinates>{},{},0</coordinates>\n'
                   '        </Point>\n'
                   '    </Placemark>\n').format(desc,
                                                location['Lon'],
                                                location['Lat'])
    points += '    </Folder>\n'

    coords = ''
    for coord in telemetry:
        coords += '{},{},0\n'.format(coord['Lon'], coord['Lat'])
    track = ('    <Placemark>\n'
             '      <name>Track</name>\n'
             '      <styleUrl>#track</styleUrl>\n'
             '      <LineString>\n'
             '        <altitudeMode>clampToGround</altitudeMode>\n'
             '        <coordinates>{coords}</coordinates>\n'
             '      </LineString>\n'
             '    </Placemark>\n').format(coords=coords)

    lats = [x['Lat'] for x in telemetry]
    lons = [x['Lon'] for x in telemetry]
    north = max(lats)
    south = min(lats)
    east = max(lons)
    west = min(lons)

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
