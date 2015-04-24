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

from collections import OrderedDict
import json
import select
import socket
import threading

import events


PORT = 12014


class Server(threading.Thread):
    def __init__(self, queue, status, database):
        threading.Thread.__init__(self)
        self.name = 'Server'

        self._queue = queue
        self._status = status
        self._database = database

        self._updates = False

        self._cmd = Cmd()

        self._client = None
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._server.bind(('', PORT))
            self._server.listen(5)
        except socket.error:
            events.Post(self._queue).error(error='Could not start server')
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
                    return
            except socket.timeout:
                return
            buf += data
            while buf.find('\n') != -1:
                line, buf = buf.split('\n', 1)
                yield line

    def __error(self, errorType, message):
        resp = OrderedDict()
        resp['Result'] = 'Error'
        resp['Type'] = errorType
        resp['Message'] = message

        self._client.sendall(json.dumps(resp))
        self._client.sendall('\r\n')

    def __result(self, method, value):
        resp = OrderedDict()
        resp['Result'] = 'OK'
        resp['Method'] = method
        resp['Value'] = value
        self._client.sendall(json.dumps(resp))
        self._client.sendall('\r\n')

    def __result_scans(self, results):
        self.__result(Cmd.SCANS, results)

    def __result_signals_last(self, results):
        self.__result(Cmd.SIGNALS_LAST, results)

    def __result_signals(self, results):
        self.__result(Cmd.SIGNALS, results)

    def __execute(self, command, method, value):
        try:
            if method == Cmd.STATUS:
                self.__result(method, self._status.get())

            elif method == Cmd.SATELLITES:
                self.__result(method, self._status.get_satellites())

            elif method == Cmd.SCAN:
                if command == Cmd.RUN:
                    events.Post(self._queue).scan()
                elif command == Cmd.DEL:
                    self._database.del_scan(self.__result_scans, value)

            elif method == Cmd.SCANS:
                if command == Cmd.GET:
                    self._database.get_scans(self.__result_scans)
                elif command == Cmd.DEL:
                    self._database.del_scans(self.__result_scans)

            elif method == Cmd.SIGNALS_LAST:
                self._database.get_signals_last(self.__result_signals_last)

            elif method == Cmd.SIGNALS:
                self._database.get_signals(self.__result_signals, value)

            elif method == Cmd.UPDATES:
                self._updates = value

        except ValueException as error:
            self.__error('Value error', error.message)

    def __get_params(self, instruction):
        command = instruction[Cmd.COMMAND]
        method = instruction[Cmd.METHOD]
        value = None
        if Cmd.VALUE in instruction:
            value = instruction[Cmd.VALUE]

        canGet = self._cmd.can_get(method)
        canSet = self._cmd.can_set(method)
        canRun = self._cmd.can_run(method)
        canDel = self._cmd.can_del(method)
        reqGet = self._cmd.req_get_val(method)
        reqSet = self._cmd.req_set_val(method)
        reqDel = self._cmd.req_del_val(method)

        try:
            if command == Cmd.GET and not canGet:
                error = '\'{}\' is not readable'.format(method)
                raise ParameterException(error)

            if command == Cmd.SET and not canSet:
                error = '\'{}\' is read only'.format(method)
                raise ParameterException(error)

            if command == Cmd.RUN and not canRun:
                error = '\'{}\' cannot be run'.format(method)
                raise ParameterException(error)

            if command == Cmd.DEL and not canDel:
                error = '\'{}\' cannot delete'.format(method)
                raise ParameterException(error)

            if command == Cmd.GET and reqGet and value is None:
                error = '\'{}\' expects a value'.format(method)
                raise ParameterException(error)

            if command == Cmd.SET and reqSet and value is None:
                error = '\'{}\' expects a value'.format(method)
                raise ParameterException(error)

            if command == Cmd.DEL and reqDel and value is None:
                error = '\'{}\' expects a value'.format(method)
                raise ParameterException(error)

        except ParameterException as error:
            self.__error('Parameter error', error.message)
            return None

        return command, method, value

    def __parse(self, data):
        try:
            instruction = json.loads(data.lower())
        except ValueError:
            self.__error('Syntax error', 'Expected a JSON string')
            return None

        try:
            if Cmd.COMMAND not in instruction:
                raise KeyException('\'Command\' not found')
            elif instruction[Cmd.COMMAND] not in Cmd.COMMANDS:
                error = 'Unknown command: {}'.format(instruction[Cmd.COMMAND])
                raise ValueException(error)

            if Cmd.METHOD not in instruction:
                raise KeyException('\'Method\' not found')
            elif instruction[Cmd.METHOD] not in Cmd.METHODS:
                error = 'Unknown method: {}'.format(instruction[Cmd.METHOD])
                raise ValueException(error)

        except KeyException as error:
            self.__error('Key error', error.message)
            return None
        except ValueException as error:
            self.__error('Value error', error.message)
            return None

        return instruction

    def run(self):
        while not self._cancel:
            if self._client is None:
                endpoints = [self._server]
            else:
                endpoints = [self._server, self._client]

            read, _write, _error = select.select(endpoints, [], [], 1)

            for sock in read:
                if sock is self._server:
                    try:
                        client, _addr = self._server.accept()
                        if self._client is not None:
                            self._client.close()

                        client.sendall('\r\nPeregrine\r\n')
                        self._client = client
                    except socket.error:
                        self._client = None
                elif sock is self._client:
                    for data in self.__read():
                        if data:
                            instruction = self.__parse(data)
                            if instruction is not None:
                                params = self.__get_params(instruction)
                                if params is not None:
                                    self.__execute(*params)
                        else:
                            self._client = None
            for sock in _error:
                if sock is self._client:
                    self._client = None
                sock.close()

    def update_scan(self, scan):
        if self._updates:
            self.__result_scans(scan)

    def close(self):
        self._cancel = True
        self._server.close()


class Cmd(object):
    # Commands
    COMMAND = 'command'
    GET = 'get'
    SET = 'set'
    RUN = 'run'
    DEL = 'del'

    # Methods
    METHOD = 'method'
    STATUS = 'status'
    SATELLITES = 'satellites'
    SCAN = 'scan'
    SCANS = 'scans'
    SIGNALS_LAST = 'signals_last'
    SIGNALS = 'signals'
    UPDATES = 'ipdates'

    VALUE = 'value'

    COMMANDS = [GET, SET, RUN, DEL]
    METHODS = [STATUS, SATELLITES, SCAN, SCANS, SIGNALS_LAST, SIGNALS, UPDATES]

    def __init__(self):
        self._params = {}
        self.__set(Cmd.STATUS, canGet=True)
        self.__set(Cmd.SATELLITES, canGet=True)
        self.__set(Cmd.SCAN, canRun=True, canDel=True, delVal=True)
        self.__set(Cmd.SCANS, canGet=True, canDel=True)
        self.__set(Cmd.SIGNALS_LAST, canGet=True)
        self.__set(Cmd.SIGNALS, canGet=True, getVal=True)
        self.__set(Cmd.UPDATES, canSet=True, setVal=True)

    def __set(self, method,
              canGet=False, canSet=False, canRun=False, canDel=False,
              setVal=False, getVal=False, delVal=False):
        self._params[method] = {'canGet': canGet,
                                'canSet': canSet,
                                'canDel': canDel,
                                'canRun': canRun,
                                'setVal': setVal,
                                'getVal': getVal,
                                'delVal': delVal}

    def can_get(self, method):
        return self._params[method]['canGet']

    def can_set(self, method):
        return self._params[method]['canSet']

    def can_run(self, method):
        return self._params[method]['canRun']

    def can_del(self, method):
        return self._params[method]['canDel']

    def req_set_val(self, method):
        return self._params[method]['setVal']

    def req_get_val(self, method):
        return self._params[method]['getVal']

    def req_del_val(self, method):
        return self._params[method]['delVal']


class KeyException(Exception):
    pass


class ValueException(Exception):
    pass


class ParameterException(Exception):
    pass
