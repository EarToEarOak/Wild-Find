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
import Queue
import sqlite3
import threading
import time

import events


VERSION = 1
APPEND, GET_SCANS, CLOSE = range(3)


class Database(threading.Thread):
    def __init__(self, path, queue):
        threading.Thread.__init__(self)
        self.name = 'Database'

        self._path = path
        self._queueParent = queue

        self._queue = Queue.Queue()

        self.start()

    def __create(self):
        self._conn = sqlite3.connect(self._path)

        with self._conn:
            cmd = 'PRAGMA foreign_keys = 1;'
            self._conn.execute(cmd)

            cmd = ('create table if not exists '
                   'Info ('
                   '    Key text primary key,'
                   '    Value blob)')
            self._conn.execute(cmd)
            try:
                cmd = 'insert into info VALUES ("DbVersion", ?)'
                self._conn.execute(cmd, (VERSION,))
            except sqlite3.IntegrityError:
                pass

            cmd = ('create table if not exists '
                   'Scans ('
                   '    TimeStamp integer primary key)')
            self._conn.execute(cmd)
            cmd = ('create table if not exists '
                   'Collars ('
                   '    Id integer primary key autoincrement,'
                   '    TimeStamp integer,'
                   '    Freq real,'
                   '    Mod integer,'
                   '    Rate real,'
                   '    Level real,'
                   '    Lon real,'
                   '    Lat real,'
                   '    foreign key (TimeStamp) REFERENCES Scans (TimeStamp))')
            self._conn.execute(cmd)

    def __append(self, **kwargs):
        with self._conn:
            timeStamp = int(kwargs['timeStamp'])
            collar = kwargs['collar']

            cmd = 'insert into Scans values(?)'
            try:
                self._conn.execute(cmd, (timeStamp,))
            except sqlite3.IntegrityError:
                pass

            cmd = 'insert into Collars values (null, ?, ?, ?, ?, ?, ?, ?)'
            self._conn.execute(cmd, (timeStamp,
                                     collar.freq,
                                     collar.mod,
                                     collar.rate,
                                     collar.level,
                                     collar.lon,
                                     collar.lat))

    def __get_scans(self):
        cursor = self._conn.cursor()
        cmd = 'select * from Scans'
        cursor.execute(cmd)
        scans = cursor.fetchall()
        events.Post(self._queueParent).db_scans(scans)

    def run(self):
        self.__create()

        while True:
            event = self._queue.get()
            eventType = event.get_type()

            if eventType == APPEND:
                self.__append(**event.get_args())
            elif eventType == GET_SCANS:
                self.__get_scans()
            elif eventType == CLOSE:
                break
            else:
                time.sleep(0.05)

        self._conn.close()

    def append(self, timeStamp, collar):
        event = events.Event(APPEND, collar=collar, timeStamp=timeStamp)
        self._queue.put(event)

    def get_scans(self):
        event = events.Event(GET_SCANS)
        self._queue.put(event)

    def stop(self):
        event = events.Event(CLOSE)
        self._queue.put(event)
