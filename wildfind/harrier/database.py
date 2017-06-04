#!/usr/bin/env python
#
#
# Wild Find
#
#
# Copyright 2014 - 2017 Al Brown
#
# Wildlife tracking and mapping
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation
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
import ctypes
import os
import platform
import sqlite3
import threading
import time

from wildfind.common.database import create_database, name_factory
from wildfind.harrier import events

GET_SCANS, \
    ADD_SIGNAL, GET_SIGNALS, \
    ADD_LOG, GET_LOG, \
    CLOSE = range(6)


class Database(threading.Thread):
    def __init__(self, path, notify):
        threading.Thread.__init__(self)
        self.name = 'Database'

        self._path = path
        self._notify = notify

        self._conn = None
        self._queue = Queue.Queue()

        if os.path.exists(path):
            print 'Appending:\t{}'.format(path)
        else:
            print 'Creating:\t{}'.format(path)

        self.start()

    def __connect(self):
        self._conn = sqlite3.connect(self._path)
        self._conn.row_factory = name_factory

        error = create_database(self._conn)
        if error is not None:
            events.Post(self._notify).error(error)

    def __add_signal(self, **kwargs):
        with self._conn:
            timeStamp = int(kwargs['timeStamp'])
            signal = kwargs['signal']
            frequency = kwargs['frequency']
            survey = kwargs['survey']

            cmd = 'insert into Scans values(?, ?, ?)'
            try:
                self._conn.execute(cmd, (timeStamp, frequency, survey))
            except sqlite3.IntegrityError:
                pass

            cmd = 'insert into Signals values (null, ?, ?, ?, ?, ?, ?, ?)'
            self._conn.execute(cmd, (timeStamp,
                                     signal.freq,
                                     signal.mod,
                                     signal.rate,
                                     signal.level,
                                     signal.lon,
                                     signal.lat))

    def __add_log(self, **kwargs):
        with self._conn:
            timeStamp = int(kwargs['timeStamp'])
            message = kwargs['message']

            cmd = 'insert into Log values (null, ?, ?)'
            self._conn.execute(cmd, (timeStamp, message))

    def __get_scans(self, callback):
        cursor = self._conn.cursor()
        cmd = 'select * from Scans'
        cursor.execute(cmd)
        scans = cursor.fetchall()
        callback(scans)

    def __get_signals(self, callback):
        cursor = self._conn.cursor()
        cmd = 'select * from Signals'
        cursor.execute(cmd)
        signals = cursor.fetchall()
        for signal in signals:
            del signal['Id']
        callback(signals)

    def __get_log(self, callback):
        cursor = self._conn.cursor()
        cmd = 'select * from Log'
        cursor.execute(cmd)
        signals = cursor.fetchall()
        for signal in signals:
            del signal['Id']

        callback(signals)

    def run(self):
        self.__connect()

        while True:
            if not self._queue.empty():
                event = self._queue.get()
                eventType = event.get_type()

                if eventType == GET_SCANS:
                    callback = event.get_arg('callback')
                    self.__get_scans(callback)
                elif eventType == ADD_SIGNAL:
                    self.__add_signal(**event.get_args())
                elif eventType == GET_SIGNALS:
                    callback = event.get_arg('callback')
                    self.__get_signals(callback)
                elif eventType == ADD_LOG:
                    self.__add_log(**event.get_args())
                elif eventType == GET_LOG:
                    callback = event.get_arg('callback')
                    self.__get_log(callback)
                elif eventType == CLOSE:
                    break
            else:
                try:
                    time.sleep(0.1)
                except IOError:
                    pass

        self._conn.close()

    def append_signal(self, timeStamp, signal, frequency, survey):
        event = events.Event(ADD_SIGNAL,
                             survey=survey,
                             signal=signal,
                             frequency=frequency,
                             timeStamp=timeStamp)
        self._queue.put(event)

    def append_log(self, message):
        timeStamp = time.time()
        event = events.Event(ADD_LOG, message=message, timeStamp=timeStamp)
        self._queue.put(event)

        return timeStamp

    def get_size(self):
        path = os.path.realpath(self._path)
        folder, _tail = os.path.split(path)

        size = os.path.getsize(path)

        space = 0
        if platform.system() == 'Windows':
            puSpace = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder),  # @UndefinedVariable
                                                       None,
                                                       None,
                                                       ctypes.pointer(puSpace))
            space = puSpace.value
        else:
            statvfs = os.statvfs(folder)  # @UndefinedVariable
            space = statvfs.f_frsize * statvfs.f_bfree

        return size, space

    def get_scans(self, callback):
        event = events.Event(GET_SCANS, callback=callback)
        self._queue.put(event)

    def get_signals(self, callback):
        event = events.Event(GET_SIGNALS, callback=callback)
        self._queue.put(event)

    def get_log(self, callback):
        event = events.Event(GET_LOG, callback=callback)
        self._queue.put(event)

    def stop(self):
        event = events.Event(CLOSE)
        self._queue.put(event)


if __name__ == '__main__':
    print 'Please run harrier.py'
    exit(1)
