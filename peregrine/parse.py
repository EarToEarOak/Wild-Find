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

import events


class Parse(object):
    # Commands
    COMMAND = 'command'
    GET = 'get'
    SET = 'set'
    REQ = 'req'
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
    LOG = 'log'

    # Values
    VALUE = 'value'
    INT, BOOL = range(2)

    COMMANDS = [GET, SET, REQ, RUN, DEL]
    METHODS = [STATUS, SATELLITES, SCAN, SCANS, SIGNALS_LAST, SIGNALS, LOG]

    def __init__(self, queue, status, database, server):
        self._queue = queue
        self._status = status
        self._database = database
        self._server = server

        self._params = {}
        self.__set(Parse.STATUS, canGet=True)
        self.__set(Parse.SATELLITES, canGet=True)
        self.__set(Parse.SCAN, canRun=True, canDel=True,
                   valDel=Parse.INT)
        self.__set(Parse.SCANS, canGet=True, canDel=True)
        self.__set(Parse.SIGNALS_LAST, canGet=True, canReq=True,
                   valReq=Parse.BOOL)
        self.__set(Parse.SIGNALS, canGet=True,
                   valGet=Parse.INT)
        self.__set(Parse.LOG, canGet=True)

    def __set(self, method,
              canGet=False, canSet=False, canReq=False,
              canRun=False, canDel=False,
              valSet=None, valGet=None, valReq=None, valDel=None):
        self._params[method] = {'canGet': canGet,
                                'canSet': canSet,
                                'canReq': canReq,
                                'canDel': canDel,
                                'canRun': canRun,
                                'valGet': valGet,
                                'valSet': valSet,
                                'valReq': valReq,
                                'valDel': valDel}

    def __can_get(self, method):
        return self._params[method]['canGet']

    def __can_set(self, method):
        return self._params[method]['canSet']

    def __can_req(self, method):
        return self._params[method]['canReq']

    def __can_run(self, method):
        return self._params[method]['canRun']

    def __can_del(self, method):
        return self._params[method]['canDel']

    def __get_get_val(self, method):
        return self._params[method]['valGet']

    def __get_set_val(self, method):
        return self._params[method]['valSet']

    def __get_req_val(self, method):
        return self._params[method]['valReq']

    def __get_del_val(self, method):
        return self._params[method]['valDel']

    def __execute(self, command, method, value):
        if method == Parse.STATUS:
            return self.result(method, self._status.get())

        elif method == Parse.SATELLITES:
            return self.result(method, self._status.get_satellites())

        elif method == Parse.SCAN:
            if command == Parse.RUN:
                events.Post(self._queue).scan()
            elif command == Parse.DEL:
                return self._database.del_scan(self.result_scans, value)

        elif method == Parse.SCANS:
            if command == Parse.GET:
                self._database.get_scans(self.result_scans)
            elif command == Parse.DEL:
                self._database.del_scans(self.result_scans)

        elif method == Parse.SIGNALS_LAST:
            if command == Parse.GET:
                self._database.get_signals_last(self.result_signals_last)
            elif command == Parse.REQ:
                self._server.set_push(value)
                return self.result(method, value)

        elif method == Parse.SIGNALS:
            self._database.get_signals(self.result_signals, value)

        elif method == Parse.LOG:
            return self.result(method, self._database.get_log(self.result_log))

    def __check_method(self, command, method, _value):
        canGet = self.__can_get(method)
        canSet = self.__can_set(method)
        canReq = self.__can_req(method)
        canDel = self.__can_del(method)

        if command == Parse.GET and canGet is None:
            error = '\'{}\' is not readable'.format(method)
            raise MethodException(error)

        elif command == Parse.SET and canSet is None:
            error = '\'{}\' is read only'.format(method)
            raise MethodException(error)

        elif command == Parse.REQ and canReq is None:
            error = '\'{}\' cannot request push updates'.format(method)
            raise MethodException(error)

        elif command == Parse.DEL and canDel is None:
            error = '\'{}\' cannot delete'.format(method)
            raise MethodException(error)

    def __check_value(self, command, method, value):
        valGet = self.__get_get_val(method)
        valSet = self.__get_set_val(method)
        valReq = self.__get_req_val(method)
        valDel = self.__get_del_val(method)

        if command == Parse.GET:
            if valGet is not None:
                if value is None:
                    error = '\'{}\' expects a value'.format(method)
                    raise ValueException(error)

        elif command == Parse.SET:
            if valSet is not None:
                if value is None:
                    error = '\'{}\' expects a value'.format(method)
                    raise ValueException(error)

        elif command == Parse.REQ:
            if valReq is not None:
                if value is None:
                    error = '\'{}\' expects a value'.format(method)
                    raise ValueException(error)

        elif command == Parse.DEL:
            if valDel is not None:
                if value is None:
                    error = '\'{}\' expects a value'.format(method)
                    raise ValueException(error)

    def __check_value_type(self, command, method, value):
        valGet = self.__get_get_val(method)
        valSet = self.__get_set_val(method)
        valReq = self.__get_req_val(method)
        valDel = self.__get_del_val(method)

        valType = None

        if command == Parse.GET:
            valType = valGet
        elif command == Parse.SET:
            valType = valSet
        elif command == Parse.REQ:
            valType = valReq
        elif command == Parse.DEL:
            valType = valDel

        if valType == Parse.INT:
            try:
                int(value)
            except ValueError:
                raise ValueException('Expected an integer')
        elif valType == Parse.BOOL:
            try:
                val = int(value)
                if val not in [True, False]:
                    raise ValueError()
            except ValueError:
                raise ValueException('Expected a boolean')

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
            raise SyntaxError('Expected a JSON string')

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

    def result(self, method, value):
        resp = OrderedDict()
        resp['Result'] = 'OK'
        resp['Method'] = method
        resp['Value'] = value

        return json.dumps(resp) + '\r\n'

    def result_error(self, errorType, message):
        resp = OrderedDict()
        resp['Result'] = 'Error'
        resp['Type'] = errorType
        resp['Message'] = message

        return json.dumps(resp) + '\r\n'

    def result_scans(self, results):
        self._server.send(self.result(Parse.SCANS, results))

    def result_signals_last(self, results):
        self._server.send(self.result(Parse.SIGNALS_LAST, results))

    def result_signals(self, results):
        self._server.send(self.result(Parse.SIGNALS, results))

    def result_log(self, results):
        self._server.send(self.result(Parse.LOG, results))


class SyntaxException(Exception):
    pass


class CommandException(Exception):
    pass


class MethodException(Exception):
    pass


class ValueException(Exception):
    pass
