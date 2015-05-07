#
# Project Peregrine
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

import sqlite3

from common.database import create_database, name_factory


class Database():
    def __init__(self):
        self._conn = None

    def __connect(self, fileName):
        self._conn = sqlite3.connect(fileName)
        self._conn.row_factory = name_factory

        create_database(self._conn)

    def open(self, fileName):
        self.__connect(fileName)

    def close(self):
        if self._conn is not None:
            self._conn.close()

    def get_scans(self):
        cursor = self._conn.cursor()
        cmd = 'select * from Scans'
        cursor.execute(cmd)

        return cursor.fetchall()

#    def get_signals(self):
#        cursor = self._conn.cursor()
#        cmd = 'select * from Signals'
#        cursor.execute(cmd)
#        signals = cursor.fetchall()
#        for signal in signals:
#            del signal['Id']
#
#        return signals

    def get_frequencies(self):
        cursor = self._conn.cursor()
        cmd = 'select Freq, count(Freq) from Signals group by Freq'
        cursor.execute(cmd)
        rows = cursor.fetchall()
        freqs = [[row['Freq'], row['count(Freq)']] for row in rows]

        return freqs


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
