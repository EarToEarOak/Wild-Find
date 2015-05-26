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

import math
import os
import sqlite3

from common.database import create_database, name_factory


class Database(object):
    def __init__(self):
        self._fileName = None
        self._conn = None

    def __connect(self, fileName):
        self._fileName = os.path.basename(fileName)
        self._conn = sqlite3.connect(fileName)
        self._conn.row_factory = name_factory

        return create_database(self._conn)

    def __filter(self, cursor, filteredSurveys, filteredScans=None, filteredSignals=None):
        condition = ' '
        condSurveys = ''
        condScans = ''
        condSignals = ''

        if len(filteredSurveys):
            cmd = 'select TimeStamp from Scans where Survey not in ('
            cmd += str(filteredSurveys).strip('[]')
            cmd += ')'
            cursor.execute(cmd)
            rows = cursor.fetchall()
            timeStamps = [row['TimeStamp'] for row in rows]

            condSurveys = ' TimeStamp in ('
            condSurveys += str(timeStamps).strip('[]')
            condSurveys += ') '

        if filteredScans is not None and len(filteredScans):
            condScans = ' TimeStamp not in ('
            condScans += str(filteredScans).strip('[]')
            condScans += ') '

        if filteredSignals is not None and len(filteredSignals):
            condSignals = ' Freq not in ('
            condSignals += str(filteredSignals).strip('[]')
            condSignals += ') '

        if len(condSurveys) or len(condScans) or len(condSignals):
            condition = ' where '
            if len(condSurveys):
                condition += condSurveys
            if len(condScans):
                if len(condSurveys):
                    condition += 'and'
                condition += condScans
            if len(condSignals):
                if len(condSurveys) or len(condScans):
                    condition += 'and'
                condition += condSignals

        return condition

    def open(self, fileName):
        return self.__connect(fileName)

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def isConnected(self):
        if self._conn is None:
            return False

        return True

    def get_filename(self):
        return self._fileName

    def get_surveys(self):
        cursor = self._conn.cursor()
        cmd = 'select * from Scans group by Survey'
        cursor.execute(cmd)
        rows = cursor.fetchall()
        surveys = [row['Survey'].encode("utf-8") for row in rows]

        return surveys

    def get_scans(self, filteredSurveys):
        if self._conn is None:
            return []

        cursor = self._conn.cursor()
        cmd = 'select * from Scans'
        cmd += self.__filter(cursor,
                             filteredSurveys)

        cursor.execute(cmd)
        rows = cursor.fetchall()
        scans = [[row['TimeStamp'], row['Freq']] for row in rows]

        return scans

    def get_signals(self, filteredSurveys, filteredSignals, filteredScans):
        if self._conn is None:
            return []

        cursor = self._conn.cursor()

        cmd = 'select Freq, Rate, count(Freq) from Signals'
        cmd += self.__filter(cursor,
                             filteredSurveys,
                             filteredScans,
                             filteredSignals)
        cmd += 'group by Freq'

        cursor.execute(cmd)
        rows = cursor.fetchall()
        signals = [[row['Freq'], row['Rate'], row['count(Freq)']]
                   for row in rows]

        return signals

    def get_locations(self, filteredSurveys, filteredScans, filteredSignals):
        if self._conn is None:
            return []

        cursor = self._conn.cursor()
        cmd = 'select Id, Freq, Rate, Level, Lon, Lat from Signals'
        cmd += self.__filter(cursor,
                             filteredSurveys,
                             filteredScans,
                             filteredSignals)
        cmd += 'order by Id'

        cursor.execute(cmd)
        rows = cursor.fetchall()
        for row in rows:
            row['Level'] = 10 * math.log(row['Level'])

        signals = [[row['Freq'], row['Rate'], row['Level'],
                    row['Lon'], row['Lat']]
                   for row in rows]

        return signals

    def get_telemetry(self, filteredSurveys, filteredScans, filteredSignals):
        if self._conn is None:
            return []

        cursor = self._conn.cursor()

        cmd = 'select Id, Lon, Lat, Level from Signals'
        cmd += self.__filter(cursor,
                             filteredSurveys,
                             filteredScans,
                             filteredSignals)
        cmd += 'order by Id'

        cursor.execute(cmd)
        rows = cursor.fetchall()
        telemetry = [[row['Lon'], row['Lat'], row['Level']] for row in rows]

        return telemetry

    def get_logs(self):
        cursor = self._conn.cursor()

        cmd = 'select * from Log'
        cursor.execute(cmd)
        rows = cursor.fetchall()
        logs = [[row['TimeStamp'], row['Message']] for row in rows]

        return logs


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
