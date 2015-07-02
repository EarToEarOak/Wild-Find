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

import select
import socket
import threading

from common.constants import PORT_HARRIER
from harrier import events
from harrier.parse import Parse


VERSION = 1


class Server(threading.Thread):
    def __init__(self, queue, status, database):
        threading.Thread.__init__(self)
        self.name = 'Server'

        self._queue = queue
        self._status = status
        self._database = database

        self._parse = Parse(queue, status, database, self)

        self._client = None
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._server.bind(('', PORT_HARRIER))
            self._server.listen(5)
        except socket.error:
            events.Post(self._queue).error('Could not start server')
            return

        self._cancel = False
        self.start()

    def __read(self):
        buf = ''
        data = True
        while data and not self._cancel:
            try:
                data = self._client.recv(1024)
                if not data:
                    self.__close_client()
                    return
            except socket.timeout:
                self.__close_client()
                return
            buf += data
            while buf.find('\n') != -1:
                line, buf = buf.split('\n', 1)
                yield line

    def __close_client(self):
        host = self.__get_client_name(self._client)
        info = '\'{}\' disconnected'.format(host)
        events.Post(self._queue).info(info)

        self._client.close()
        self._client = None

    def __get_client_name(self, client):
        return socket.gethostbyaddr(client.getpeername()[0])[0]

    def run(self):
        while not self._cancel:
            if self._client is None:
                endpoints = [self._server]
            else:
                endpoints = [self._server, self._client]

            read, _write, error = select.select(endpoints, [], [], 0.5)

            for sock in read:
                if sock is self._server:
                    try:
                        client, _addr = self._server.accept()
                        if self._client is not None:
                            self._client.close()

                        self._client = client
                        result = self._parse.result_connect(VERSION)
                        self.send(result)

                        host = self.__get_client_name(client)
                        info = 'Connection from \'{}\''.format(host)
                        events.Post(self._queue).info(info)
                    except socket.error:
                        self._client = None
                elif sock is self._client:
                    for line in self.__read():
                        if line:
                            result = self._parse.parse(line)
                            self.send(result)

            for sock in error:
                if sock is self._client:
                    self._client = None
                sock.close()

    def send(self, result):
        if result is not None and self._client is not None:
            try:
                self._client.sendall(result)
            except socket.error:
                self.__close_client()

    def send_signals(self, timeStamp, signals):
        resp = []
        for signal in signals:
            resp.append(signal.get_dict(timeStamp))

        sigs = self._parse.result_signals(resp)
        self.send(sigs)

    def send_status(self):
        status = self._parse.result('Status', self._status.get())
        self.send(status)

    def send_sats(self):
        sats = self._parse.result('Satellites', self._status.get_satellites())
        self.send(sats)

    def send_log(self, timeStamp, message):
        entry = {'TimeStamp': timeStamp,
                 'Message': message}
        self._parse.result_log([entry])

    def stop(self):
        self._cancel = True
        self._server.close()


if __name__ == '__main__':
    print 'Please run harrier.py'
    exit(1)
