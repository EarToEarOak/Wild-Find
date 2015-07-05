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

from collections import OrderedDict
import json

from harrier import events


class Parse(object):
    # Commands
    COMMAND = 'command'
    GET = 'get'
    SET = 'set'
    RUN = 'run'

    # Methods
    METHOD = 'method'
    SCAN = 'scan'
    SCANS = 'scans'
    SIGNALS = 'signals'
    LOG = 'log'
    SETTINGS = 'settings'
    DELAY = 'delay'
    FREQUENCY = 'frequency'

    # Values
    VALUE = 'value'
    FLOAT = range(1)

    COMMANDS = [GET, SET, RUN]
    METHODS = [SCAN, SCANS, SIGNALS, LOG, SETTINGS, DELAY, FREQUENCY]

    def __init__(self, queue, status, database, settings, server):
        self._queue = queue
        self._status = status
        self._database = database
        self._settings = settings
        self._server = server

        self._params = {}
        self.__set(Parse.SCAN, canRun=True)
        self.__set(Parse.SCANS, canGet=True)
        self.__set(Parse.SIGNALS, canGet=True)
        self.__set(Parse.LOG, canGet=True)
        self.__set(Parse.SETTINGS, canGet=True)
        self.__set(Parse.DELAY, canSet=True, valSet=Parse.FLOAT)
        self.__set(Parse.FREQUENCY, canSet=True, valSet=Parse.FLOAT)

    def __set(self, method, canGet=False, canSet=False, canRun=False,
              valSet=None):
        self._params[method] = {'canGet': canGet,
                                'canSet': canSet,
                                'canRun': canRun,
                                'valSet': valSet}

    def __execute(self, command, method, value):
        if method == Parse.SCAN:
            if command == Parse.RUN:
                events.Post(self._queue).scan()

        elif method == Parse.SCANS:
            self._database.get_scans(self.result_scans)

        elif method == Parse.SIGNALS:
            self._database.get_signals(self.result_signals)

        elif method == Parse.LOG:
            return self.result(method, self._database.get_log(self.result_log))

        elif method == Parse.SETTINGS:
            if command == Parse.GET:
                return self.result(method, self._settings.get())

        elif method == Parse.DELAY:
            if command == Parse.SET:
                if value < 0:
                    value = None
                self._settings.delay = value
                return self.result(method)

        elif method == Parse.FREQUENCY:
            if command == Parse.SET:
                self._settings.freq = value
                return self.result(method)

    def __check_method(self, command, method, _value):
        canGet = self._params[method]['canGet']
        canSet = self._params[method]['canSet']
        canRun = self._params[method]['canRun']

        if command == Parse.GET and not canGet:
            error = '\'{}\' is not readable'.format(method)
            raise MethodException(error)

        if command == Parse.SET and not canSet:
            error = '\'{}\' is not writable'.format(method)
            raise MethodException(error)

        elif command == Parse.RUN and not canRun:
            error = '\'{}\' cannot be run'.format(method)
            raise MethodException(error)

    def __check_value(self, command, method, value):
        valSet = self._params[method]['valSet']

        if command == Parse.GET:
            if value is not None:
                error = '\'{}\' has an unexpected value'.format(method)
                raise ValueException(error)

        elif command == Parse.SET:
            if valSet is not None:
                if value is None:
                    error = '\'{}\' expects a value'.format(method)
                    raise ValueException(error)

    def __check_value_type(self, command, method, value):
        valSet = self._params[method]['valSet']

        valType = None
        if command == Parse.SET:
            valType = valSet

        if valType == Parse.FLOAT:
            try:
                float(value)
            except ValueError:
                raise ValueException('Expected a float')

    def __get_params(self, instruction):
        command = instruction[Parse.COMMAND]
        method = instruction[Parse.METHOD]
        value = None
        if Parse.VALUE in instruction:
            value = instruction[Parse.VALUE]

        return command, method, value

    def __parse(self, data):
        try:
            instruction = json.loads(data.lower())
        except ValueError:
            raise SyntaxException('Expected a JSON string')

        if Parse.COMMAND not in instruction:
            raise CommandException('\'Command\' not found')
        elif instruction[Parse.COMMAND] not in Parse.COMMANDS:
            error = 'Unknown command: {}'.format(instruction[Parse.COMMAND])
            raise CommandException(error)

        if Parse.METHOD not in instruction:
            raise MethodException('\'Method\' not found')
        elif instruction[Parse.METHOD] not in Parse.METHODS:
            error = 'Unknown method: {}'.format(instruction[Parse.METHOD])
            raise MethodException(error)

        return instruction

    def parse(self, line):
        try:
            instruction = self.__parse(line)
            params = self.__get_params(instruction)
            self.__check_method(*params)
            self.__check_value(*params)
            self.__check_value_type(*params)
            return self.__execute(*params)

        except SyntaxException as error:
            return self.result_error('Syntax error', error.message)
        except CommandException as error:
            return self.result_error('Command error', error.message)
        except MethodException as error:
            return self.result_error('Method error', error.message)
        except ValueException as error:
            return self.result_error('Value error', error.message)

    def result(self, method, value=None):
        resp = OrderedDict()
        resp['Result'] = 'OK'
        resp['Method'] = method.capitalize()
        if value is not None:
            resp['Value'] = value

        return json.dumps(resp) + '\r\n'

    def result_connect(self, version):
        resp = OrderedDict()
        resp['Method'] = 'Connect'
        resp['Result'] = 'OK'
        resp['Application'] = 'Harrier'
        resp['Version'] = version

        return json.dumps(resp) + '\r\n'

    def result_error(self, errorType, message):
        resp = OrderedDict()
        resp['Result'] = 'Error'
        resp['Type'] = errorType
        resp['Message'] = message

        return json.dumps(resp) + '\r\n'

    def result_scans(self, scans):
        self._server.send(self.result(Parse.SCANS, scans))

    def result_signals(self, signals):
        self._server.send(self.result(Parse.SIGNALS, signals))

    def result_log(self, log):
        self._server.send(self.result(Parse.LOG, log))


class SyntaxException(Exception):
    pass


class CommandException(Exception):
    pass


class MethodException(Exception):
    pass


class ValueException(Exception):
    pass


if __name__ == '__main__':
    print 'Please run harrier.py'
    exit(1)
